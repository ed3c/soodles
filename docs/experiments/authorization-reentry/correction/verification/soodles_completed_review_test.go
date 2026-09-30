package loop

import (
	"context"
	"os"
	"path/filepath"
	"reflect"
	"testing"
	"time"

	"github.com/poteto/noodle/config"
	"github.com/poteto/noodle/event"
	"github.com/poteto/noodle/internal/orderx"
	"github.com/poteto/noodle/internal/state"
	"github.com/poteto/noodle/mise"
	loopruntime "github.com/poteto/noodle/runtime"
)

// This experiment tests the exact completed-outcome recovery missing from the
// blocked-outcome edit/requeue control. It is not installed in Noodle.
func TestSoodlesCompletedReviewRestartAndRequestChanges(t *testing.T) {
	l, _, cook := newTypedOutcomeTestLoop(t)
	runGitInRepo(t, l.projectDir, "init", "-b", "main")
	runGitInRepo(t, l.projectDir, "config", "user.email", "test@noodle.dev")
	runGitInRepo(t, l.projectDir, "config", "user.name", "Noodle Test")
	runGitInRepo(t, l.projectDir, "commit", "--allow-empty", "-m", "base")
	runGitInRepo(t, l.projectDir, "worktree", "add", "-b", cook.worktreeName, cook.worktreePath)
	runGitInRepo(t, cook.worktreePath, "commit", "--allow-empty", "-m", "candidate")
	head := gitOutputInRepo(t, cook.worktreePath, "rev-parse", "HEAD")
	appendTypedOutcome(t, l, cook, event.StageOutcomeCompleted, false, cook.orderID, cook.stageIndex)
	dir := filepath.Join(l.runtimeDir, "sessions", cook.session.ID())
	for name, data := range map[string]string{
		"spawn.json": `{"session_id":"session-1","worktree_path":"` + cook.worktreePath + `","retry_count":0}`,
		"prompt.txt": "original prompt", "process.json": `{"session_id":"session-1","pid":99999999}`,
	} {
		if err := os.WriteFile(filepath.Join(dir, name), []byte(data), 0600); err != nil {
			t.Fatal(err)
		}
	}
	if err := l.parkPendingReview(cook, "typed completed"); err != nil {
		t.Fatal(err)
	}
	restarted := New(l.projectDir, "noodle", l.config, l.deps)
	if err := restarted.reconcile(context.Background()); err != nil {
		t.Fatal(err)
	}
	if _, ok := restarted.cooks.pendingReview[cook.orderID]; !ok {
		t.Fatal("lost completed review")
	}
	originalAttempts := append([]state.AttemptNode(nil), restarted.canonical.Orders[cook.orderID].Stages[0].Attempts...)
	if err := restarted.controlRequestChanges(cook.orderID, "failed exact-head runtime"); err != nil {
		t.Fatal(err)
	}
	order := restarted.canonical.Orders[cook.orderID]
	if order.Status != state.OrderFailed || order.Stages[cook.stageIndex].Status != state.StageFailed {
		t.Fatalf("not failed after request-changes: %+v", order)
	}
	if got := gitOutputInRepo(t, cook.worktreePath, "rev-parse", "HEAD"); got != head {
		t.Fatalf("candidate changed: %s != %s", got, head)
	}
	next := filepath.Join(l.runtimeDir, "orders-next.json")
	writeCompactOrders(t, next, orderx.CompactOrdersFile{Orders: []orderx.CompactOrder{{
		ID: cook.orderID, Title: "correct same issue",
		Stages: []orderx.CompactStage{{Do: "execute", With: cook.stage.Provider,
			Model: cook.stage.Model, Prompt: "fresh admitted projection"}},
	}}})
	promoted := consumeOrdersNextAndPersist(t, next, filepath.Join(l.runtimeDir, "orders.json"))
	if !promoted.Promoted {
		t.Fatal("same failed order was not promoted")
	}
	for _, promotedOrder := range promoted.Orders.Orders {
		restarted.syncCanonicalOrderFromLegacy(promotedOrder)
	}
	canonical := restarted.canonical.Orders[cook.orderID]
	failedAttempts := append([]state.AttemptNode(nil), order.Stages[0].Attempts...)
	if len(failedAttempts) != len(originalAttempts) || failedAttempts[0].SessionID != originalAttempts[0].SessionID || failedAttempts[0].Status != state.AttemptFailed {
		t.Fatalf("failed attempt identity mismatch: %+v", failedAttempts)
	}
	if canonical.Stages[0].Status != state.StagePending || !reflect.DeepEqual(canonical.Stages[0].Attempts, failedAttempts) {
		t.Fatalf("replacement must preserve failed attempt history: %+v", canonical)
	}
	var replacement *orderx.Order
	for i := range promoted.Orders.Orders {
		if promoted.Orders.Orders[i].ID == cook.orderID {
			replacement = &promoted.Orders.Orders[i]
		}
	}
	if replacement == nil || replacement.Status != orderx.OrderStatusActive ||
		len(replacement.Stages) != 1 || replacement.Stages[0].Prompt != "fresh admitted projection" {
		t.Fatalf("wrong replacement: %+v", replacement)
	}
}

// An acknowledgement is not a transition receipt: a concurrent scheduler can
// occupy the single slot and make request-changes return success without acting.
func TestSoodlesRequestChangesAckCanLeaveReviewUnchanged(t *testing.T) {
	l := newControlTestLoop(t, &fakeWorktree{}, newMockRuntime())
	l.config.Concurrency.MaxConcurrency = 1
	l.cooks.activeCooksByOrder["schedule"] = &cookHandle{}
	ack := l.processControlLine(`{"id":"soodles-correction","action":"request-changes","order_id":"42"}`)
	if ack.Status != "ok" {
		t.Fatalf("ack status = %q, want ok", ack.Status)
	}
	if _, ok := l.cooks.pendingReview["42"]; !ok {
		t.Fatal("deferred request-changes unexpectedly cleared review")
	}
	orders, err := readOrders(l.deps.OrdersFile)
	if err != nil {
		t.Fatal(err)
	}
	if len(orders.Orders) != 1 || orders.Orders[0].Status != OrderStatusActive {
		t.Fatalf("deferred request-changes changed order: %+v", orders.Orders)
	}
}

// Restored canonical mode wins over config. Only the process hold prevents
// dispatch until the existing explicit mode control releases it.
func TestSoodlesManualConfigCannotHoldCanonicalSupervisedMode(t *testing.T) {
	projectDir := t.TempDir()
	ordersPath := filepath.Join(projectDir, ".noodle", "orders.json")
	orders := OrdersFile{Orders: []Order{{
		ID: "fresh-correction", Status: OrderStatusActive,
		Stages: []Stage{{TaskKey: "execute", Skill: "execute", Provider: "claude",
			Model: "claude-opus-4-6", Status: StageStatusPending}},
	}}}
	if err := writeOrdersAtomic(ordersPath, orders); err != nil {
		t.Fatal(err)
	}
	cfg := config.DefaultConfig()
	cfg.Mode = "supervised"
	deps := Dependencies{Runtimes: map[string]loopruntime.Runtime{"process": newMockRuntime()},
		Worktree: &fakeWorktree{}, Adapter: &fakeAdapterRunner{}, Mise: &fakeMise{},
		Monitor: fakeMonitor{}, Registry: testLoopRegistry(), Now: time.Now, OrdersFile: ordersPath}
	previous := New(projectDir, "noodle", cfg, deps)
	if err := previous.loadOrBootstrapCanonical(); err != nil {
		t.Fatal(err)
	}
	cfg.Mode = "manual"
	l := New(projectDir, "noodle", cfg, deps)
	plan, err := l.planCycleSpawns(orders, mise.Brief{}, 1)
	if err != nil || len(plan) != 1 {
		t.Fatalf("config alone: plan=%+v err=%v, want one spawn", plan, err)
	}
	l.deps.ModeOverride = state.RunModeManual
	plan, err = l.planCycleSpawns(orders, mise.Brief{}, 1)
	if err != nil || len(plan) != 0 {
		t.Fatalf("process hold: plan=%+v err=%v, want no spawn", plan, err)
	}
	if err := l.controlMode(string(state.RunModeSupervised)); err != nil {
		t.Fatal(err)
	}
	plan, err = l.planCycleSpawns(orders, mise.Brief{}, 1)
	if err != nil || len(plan) != 1 {
		t.Fatalf("explicit release: plan=%+v err=%v, want one spawn", plan, err)
	}
}
