
function test_dataset() {
    QUnit.test( "task  tests", function( assert ) {
        console.log(task, task.item_name)
        assert.ok(task.item_name == "test", "Task name test passed!");
    });
}
