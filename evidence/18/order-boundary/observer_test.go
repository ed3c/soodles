package loop
import (
 "os"
 "path/filepath"
 "testing"
 "github.com/poteto/noodle/internal/orderx"
)
// External #18 requirement observer, not a test of an already-promised Noodle API.
func TestSoodles18StaleInitialProposalCannotRestart(t *testing.T) {
 dir:=t.TempDir(); next:=filepath.Join(dir,"orders-next.json")
 proposal:=[]byte(`{"orders":[{"id":"soodles-18","stages":[{"do":"execute","with":"codex","model":"gpt-5.6-sol"}]}]}`)
 // Producer observes absence and prepares its initial proposal.
 if err:=os.WriteFile(next,proposal,0600);err!=nil{t.Fatal(err)}
 first,err:=consumeOrdersNext(next,OrdersFile{});if err!=nil{t.Fatal(err)}
 // Owner consumes it; crash before deleting proposal leaves the same bytes.
 failed,err:=failStage(first.Orders,"soodles-18","physical interruption");if err!=nil{t.Fatal(err)}
 if err:=orderx.WriteOrdersAtomic(filepath.Join(dir,"orders.json"),failed);err!=nil{t.Fatal(err)}
 // Re-read durable owner state; replay the original initial-admission bytes.
 durable,err:=orderx.ReadOrders(filepath.Join(dir,"orders.json"));if err!=nil{t.Fatal(err)}
 before:=durable.Orders[0].Status
 if before!=OrderStatusFailed{t.Fatal("fixture did not persist failed state")}
 replay,err:=consumeOrdersNext(next,durable);if err!=nil{t.Fatal(err)}
 t.Logf("before=%s after=%s dispatchable=%d",before,replay.Orders.Orders[0].Status,len(dispatchableStages(replay.Orders,nil,nil,nil)))
 if replay.Orders.Orders[0].Status!=OrderStatusFailed || len(dispatchableStages(replay.Orders,nil,nil,nil))!=0 {t.Fatal("stale initial proposal restarted failed canonical work without new authorization")}
}
func TestSoodles18IndependentInitialProposal(t *testing.T) {
 dir:=t.TempDir(); next:=filepath.Join(dir,"orders-next.json")
 if err:=os.WriteFile(next,[]byte(`{"orders":[{"id":"soodles-19","stages":[{"do":"execute","with":"codex","model":"gpt-5.6-sol"}]}]}`),0600);err!=nil{t.Fatal(err)}
 result,err:=consumeOrdersNext(next,OrdersFile{});if err!=nil{t.Fatal(err)}
 if len(result.Orders.Orders)!=1 || len(dispatchableStages(result.Orders,nil,nil,nil))!=1 {t.Fatal("independent initial work not admitted")}
}
