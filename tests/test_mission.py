"""Tests for Mission Runtime — mission, goal_tree, task_graph, progress_tracker, mission_runtime."""

import time
import unittest
from prototype.common import Event, EventBus


# ═══════════════════════════════════════════════════════════════════════════════
#  Mission
# ═══════════════════════════════════════════════════════════════════════════════

class TestMission(unittest.TestCase):
    def setUp(self):
        from prototype.mission.mission import Mission, MissionStatus, MissionPriority
        self.Mission = Mission
        self.MissionStatus = MissionStatus
        self.MissionPriority = MissionPriority

    def test_create_mission(self):
        m = self.Mission(name="Test Mission", description="desc")
        assert m.name == "Test Mission"
        assert m.status == self.MissionStatus.CREATED
        assert m.priority == self.MissionPriority.NORMAL
        assert m.id

    def test_activate(self):
        m = self.Mission(name="m")
        m.activate()
        assert m.status == self.MissionStatus.ACTIVE

    def test_activate_from_paused(self):
        m = self.Mission(name="m")
        m.activate()
        m.pause()
        m.resume()
        assert m.status == self.MissionStatus.ACTIVE

    def test_activate_invalid_state(self):
        m = self.Mission(name="m")
        m.activate()
        m.complete()
        with self.assertRaises(ValueError):
            m.activate()

    def test_pause(self):
        m = self.Mission(name="m")
        m.activate()
        m.pause()
        assert m.status == self.MissionStatus.PAUSED

    def test_pause_invalid_state(self):
        m = self.Mission(name="m")
        with self.assertRaises(ValueError):
            m.pause()

    def test_resume(self):
        m = self.Mission(name="m")
        m.activate()
        m.pause()
        m.resume()
        assert m.status == self.MissionStatus.ACTIVE

    def test_resume_invalid_state(self):
        m = self.Mission(name="m")
        with self.assertRaises(ValueError):
            m.resume()

    def test_complete(self):
        m = self.Mission(name="m")
        m.activate()
        m.complete()
        assert m.status == self.MissionStatus.COMPLETED
        assert m.context.completed_at is not None

    def test_complete_invalid_state(self):
        m = self.Mission(name="m")
        with self.assertRaises(ValueError):
            m.complete()

    def test_fail(self):
        m = self.Mission(name="m")
        m.activate()
        m.fail("reason")
        assert m.status == self.MissionStatus.FAILED
        assert m.metadata["failure_reason"] == "reason"

    def test_fail_from_created(self):
        m = self.Mission(name="m")
        m.fail("reason")
        assert m.status == self.MissionStatus.FAILED

    def test_fail_completed_invalid(self):
        m = self.Mission(name="m")
        m.activate()
        m.complete()
        with self.assertRaises(ValueError):
            m.fail("reason")

    def test_cancel(self):
        m = self.Mission(name="m")
        m.cancel()
        assert m.status == self.MissionStatus.CANCELLED

    def test_cancel_completed_invalid(self):
        m = self.Mission(name="m")
        m.activate()
        m.complete()
        with self.assertRaises(ValueError):
            m.cancel()

    def test_task_accounting(self):
        m = self.Mission(name="m")
        m.set_total_tasks(5)
        assert m.context.total_tasks == 5
        m.record_task_completed()
        m.record_task_completed()
        m.record_task_failed()
        assert m.context.completed_tasks == 2
        assert m.context.failed_tasks == 1

    def test_to_dict(self):
        m = self.Mission(name="m", description="d")
        d = m.to_dict()
        assert d["name"] == "m"
        assert d["description"] == "d"
        assert d["status"] == "created"

    def test_from_dict(self):
        m = self.Mission(name="m")
        d = m.to_dict()
        restored = self.Mission.from_dict(d)
        assert restored.name == "m"
        assert restored.id == m.id
        assert restored.status == m.status

    def test_priority(self):
        m = self.Mission(name="m", priority=self.MissionPriority.CRITICAL)
        assert m.priority.value == 3

    def test_parent_id(self):
        m = self.Mission(name="m", parent_id="parent-123")
        assert m.parent_id == "parent-123"


# ═══════════════════════════════════════════════════════════════════════════════
#  GoalTree
# ═══════════════════════════════════════════════════════════════════════════════

class TestGoalTree(unittest.TestCase):
    def setUp(self):
        from prototype.mission.goal_tree import GoalTree, GoalStatus
        self.GoalTree = GoalTree
        self.GoalStatus = GoalStatus

    def test_add_root_goal(self):
        tree = self.GoalTree()
        g = tree.add_goal("root")
        assert g.name == "root"
        assert g.is_root()
        assert tree.count() == 1

    def test_add_child_goal(self):
        tree = self.GoalTree()
        root = tree.add_goal("root")
        child = tree.add_goal("child", parent_id=root.id)
        assert child.parent_id == root.id
        assert not child.is_root()
        assert child.is_leaf()
        assert tree.count() == 2

    def test_get_children(self):
        tree = self.GoalTree()
        root = tree.add_goal("root")
        c1 = tree.add_goal("c1", parent_id=root.id)
        c2 = tree.add_goal("c2", parent_id=root.id)
        children = tree.get_children(root.id)
        assert len(children) == 2
        ids = {c.id for c in children}
        assert c1.id in ids
        assert c2.id in ids

    def test_get_parents(self):
        tree = self.GoalTree()
        root = tree.add_goal("root")
        child = tree.add_goal("child", parent_id=root.id)
        grandchild = tree.add_goal("grandchild", parent_id=child.id)
        parents = tree.get_parents(grandchild.id)
        assert len(parents) == 2
        assert parents[0].id == child.id
        assert parents[1].id == root.id

    def test_get_root_goals(self):
        tree = self.GoalTree()
        r1 = tree.add_goal("r1")
        r2 = tree.add_goal("r2")
        child = tree.add_goal("child", parent_id=r1.id)
        roots = tree.get_root_goals()
        assert len(roots) == 2

    def test_remove_goal(self):
        tree = self.GoalTree()
        root = tree.add_goal("root")
        child = tree.add_goal("child", parent_id=root.id)
        assert tree.remove_goal(root.id)
        assert tree.count() == 0

    def test_remove_nonexistent(self):
        tree = self.GoalTree()
        assert not tree.remove_goal("nope")

    def test_update_status(self):
        tree = self.GoalTree()
        g = tree.add_goal("g")
        assert tree.update_status(g.id, self.GoalStatus.ACTIVE)
        assert tree.get_goal(g.id).status == self.GoalStatus.ACTIVE

    def test_assign_task(self):
        tree = self.GoalTree()
        g = tree.add_goal("g")
        assert tree.assign_task(g.id, "task-1")
        assert "task-1" in tree.get_goal(g.id).task_ids

    def test_completion_ratio_leaf(self):
        tree = self.GoalTree()
        g = tree.add_goal("g")
        assert tree.get_completion_ratio(g.id) == 0.0
        tree.update_status(g.id, self.GoalStatus.COMPLETED)
        assert tree.get_completion_ratio(g.id) == 1.0

    def test_completion_ratio_parent(self):
        tree = self.GoalTree()
        root = tree.add_goal("root")
        c1 = tree.add_goal("c1", parent_id=root.id)
        c2 = tree.add_goal("c2", parent_id=root.id)
        tree.update_status(c1.id, self.GoalStatus.COMPLETED)
        # 1/2 completed = 0.5
        ratio = tree.get_completion_ratio(root.id)
        assert abs(ratio - 0.5) < 0.01

    def test_is_complete(self):
        tree = self.GoalTree()
        root = tree.add_goal("root")
        c1 = tree.add_goal("c1", parent_id=root.id)
        assert not tree.is_complete(root.id)
        tree.update_status(c1.id, self.GoalStatus.COMPLETED)
        assert tree.is_complete(root.id)

    def test_get_all_tasks(self):
        tree = self.GoalTree()
        root = tree.add_goal("root")
        tree.assign_task(root.id, "t1")
        child = tree.add_goal("child", parent_id=root.id)
        tree.assign_task(child.id, "t2")
        tasks = tree.get_all_tasks(root.id)
        assert set(tasks) == {"t1", "t2"}

    def test_get_goals_by_status(self):
        tree = self.GoalTree()
        g1 = tree.add_goal("g1")
        g2 = tree.add_goal("g2")
        tree.update_status(g1.id, self.GoalStatus.COMPLETED)
        completed = tree.get_goals_by_status(self.GoalStatus.COMPLETED)
        assert len(completed) == 1
        assert completed[0].id == g1.id

    def test_serialization(self):
        tree = self.GoalTree()
        root = tree.add_goal("root")
        child = tree.add_goal("child", parent_id=root.id)
        data = tree.to_dict()
        restored = self.GoalTree.from_dict(data)
        assert restored.count() == 2
        assert len(restored.get_root_goals()) == 1


# ═══════════════════════════════════════════════════════════════════════════════
#  TaskGraph
# ═══════════════════════════════════════════════════════════════════════════════

class TestTaskGraph(unittest.TestCase):
    def setUp(self):
        from prototype.mission.task_graph import TaskGraph, TaskStatus
        self.TaskGraph = TaskGraph
        self.TaskStatus = TaskStatus

    def test_add_task(self):
        g = self.TaskGraph()
        t = g.add_task("task1")
        assert t.name == "task1"
        assert g.count() == 1

    def test_add_with_dependencies(self):
        g = self.TaskGraph()
        t1 = g.add_task("t1")
        t2 = g.add_task("t2", dependencies=[t1.id])
        assert t2.dependencies == [t1.id]
        assert t1.dependents == [t2.id]

    def test_get_ready_tasks(self):
        g = self.TaskGraph()
        t1 = g.add_task("t1")
        t2 = g.add_task("t2", dependencies=[t1.id])
        ready = g.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].id == t1.id

    def test_get_ready_after_completion(self):
        g = self.TaskGraph()
        t1 = g.add_task("t1")
        t2 = g.add_task("t2", dependencies=[t1.id])
        g.update_status(t1.id, self.TaskStatus.COMPLETED)
        ready = g.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].id == t2.id

    def test_remove_task(self):
        g = self.TaskGraph()
        t1 = g.add_task("t1")
        t2 = g.add_task("t2", dependencies=[t1.id])
        assert g.remove_task(t1.id)
        assert g.count() == 1
        assert t2.dependencies == []

    def test_remove_nonexistent(self):
        g = self.TaskGraph()
        assert not g.remove_task("nope")

    def test_has_cycle(self):
        g = self.TaskGraph()
        t1 = g.add_task("t1")
        t2 = g.add_task("t2")
        t3 = g.add_task("t3")
        g._tasks[t1.id].dependents.append(t2.id)
        g._tasks[t1.id].dependencies.append(t3.id)
        g._tasks[t2.id].dependents.append(t3.id)
        g._tasks[t2.id].dependencies.append(t1.id)
        g._tasks[t3.id].dependents.append(t1.id)
        g._tasks[t3.id].dependencies.append(t2.id)
        assert g.has_cycle()

    def test_no_cycle(self):
        g = self.TaskGraph()
        t1 = g.add_task("t1")
        t2 = g.add_task("t2", dependencies=[t1.id])
        assert not g.has_cycle()

    def test_topological_order(self):
        g = self.TaskGraph()
        t1 = g.add_task("t1")
        t2 = g.add_task("t2", dependencies=[t1.id])
        t3 = g.add_task("t3", dependencies=[t2.id])
        order = g.topological_order()
        assert order.index(t1.id) < order.index(t2.id) < order.index(t3.id)

    def test_completion_ratio(self):
        g = self.TaskGraph()
        t1 = g.add_task("t1")
        t2 = g.add_task("t2")
        g.update_status(t1.id, self.TaskStatus.COMPLETED)
        assert abs(g.get_completion_ratio() - 0.5) < 0.01

    def test_is_complete(self):
        g = self.TaskGraph()
        t1 = g.add_task("t1")
        assert not g.is_complete()
        g.update_status(t1.id, self.TaskStatus.COMPLETED)
        assert g.is_complete()

    def test_is_complete_with_skipped(self):
        g = self.TaskGraph()
        t1 = g.add_task("t1")
        t2 = g.add_task("t2")
        g.update_status(t1.id, self.TaskStatus.COMPLETED)
        g.update_status(t2.id, self.TaskStatus.SKIPPED)
        assert g.is_complete()

    def test_get_tasks_by_status(self):
        g = self.TaskGraph()
        t1 = g.add_task("t1")
        t2 = g.add_task("t2")
        g.update_status(t1.id, self.TaskStatus.RUNNING)
        running = g.get_tasks_by_status(self.TaskStatus.RUNNING)
        assert len(running) == 1

    def test_get_dependents_and_dependencies(self):
        g = self.TaskGraph()
        t1 = g.add_task("t1")
        t2 = g.add_task("t2", dependencies=[t1.id])
        deps = g.get_dependencies(t2.id)
        assert len(deps) == 1
        dependents = g.get_dependents(t1.id)
        assert len(dependents) == 1

    def test_serialization(self):
        g = self.TaskGraph()
        t1 = g.add_task("t1", action="do_something")
        t2 = g.add_task("t2", dependencies=[t1.id])
        data = g.to_dict()
        restored = self.TaskGraph.from_dict(data)
        assert restored.count() == 2


# ═══════════════════════════════════════════════════════════════════════════════
#  ProgressTracker
# ═══════════════════════════════════════════════════════════════════════════════

class TestProgressTracker(unittest.TestCase):
    def setUp(self):
        from prototype.mission.progress_tracker import ProgressTracker
        self.ProgressTracker = ProgressTracker

    def test_start_and_stop_tracking(self):
        pt = self.ProgressTracker()
        pt.start_tracking("m1")
        assert "m1" in pt._start_times
        pt.stop_tracking("m1")
        assert "m1" not in pt._start_times

    def test_record_snapshot(self):
        from prototype.mission.progress_tracker import ProgressSnapshot
        pt = self.ProgressTracker()
        snap = ProgressSnapshot(mission_id="m1", overall_progress=0.5)
        pt.record_snapshot(snap)
        latest = pt.get_latest_snapshot("m1")
        assert latest.overall_progress == 0.5

    def test_calculate_progress(self):
        pt = self.ProgressTracker()
        pt.start_tracking("m1")
        snap = pt.calculate_progress("m1", 0.5, {
            "total": 10, "completed": 5, "failed": 0,
            "active": 1, "pending": 4, "blocked": 0,
        })
        assert snap.task_completion == 0.5
        assert snap.goal_completion == 0.5
        assert snap.overall_progress > 0

    def test_calculate_progress_empty(self):
        pt = self.ProgressTracker()
        pt.start_tracking("m1")
        snap = pt.calculate_progress("m1", 0.0, {"total": 0, "completed": 0})
        assert snap.task_completion == 0.0

    def test_history(self):
        pt = self.ProgressTracker()
        pt.start_tracking("m1")
        pt.calculate_progress("m1", 0.3, {"total": 10, "completed": 3})
        pt.calculate_progress("m1", 0.6, {"total": 10, "completed": 6})
        history = pt.get_history("m1")
        assert len(history) == 2

    def test_clear(self):
        pt = self.ProgressTracker()
        pt.start_tracking("m1")
        pt.clear("m1")
        assert pt.get_latest_snapshot("m1") is None


# ═══════════════════════════════════════════════════════════════════════════════
#  MissionRuntime
# ═══════════════════════════════════════════════════════════════════════════════

class TestMissionRuntime(unittest.TestCase):
    def setUp(self):
        from prototype.mission.mission_runtime import MissionRuntime
        self.bus = EventBus()
        self.runtime = MissionRuntime(event_bus=self.bus)
        self.runtime.load()

    def tearDown(self):
        self.runtime.shutdown()

    def test_load_and_lifecycle(self):
        assert self.runtime.is_loaded()
        self.runtime.shutdown()
        assert not self.runtime.is_loaded()
        self.runtime.shutdown()  # idempotent

    def test_create_mission(self):
        m = self.runtime.create_mission("test mission", description="desc")
        assert m.name == "test mission"
        assert m.status.value == "created"

    def test_get_mission(self):
        m = self.runtime.create_mission("m")
        fetched = self.runtime.get_mission(m.id)
        assert fetched is not None
        assert fetched.name == "m"

    def test_list_missions(self):
        self.runtime.create_mission("m1")
        self.runtime.create_mission("m2")
        missions = self.runtime.list_missions()
        assert len(missions) == 2

    def test_list_missions_by_status(self):
        from prototype.mission.mission import MissionStatus
        m1 = self.runtime.create_mission("m1")
        m2 = self.runtime.create_mission("m2")
        self.runtime.activate_mission(m1.id)
        active = self.runtime.list_missions(status=MissionStatus.ACTIVE)
        assert len(active) == 1
        assert active[0].id == m1.id

    def test_delete_mission(self):
        m = self.runtime.create_mission("m")
        assert self.runtime.delete_mission(m.id)
        assert self.runtime.get_mission(m.id) is None

    def test_delete_nonexistent(self):
        assert not self.runtime.delete_mission("nope")

    def test_activate_mission(self):
        m = self.runtime.create_mission("m")
        m = self.runtime.activate_mission(m.id)
        assert m.status.value == "active"
        assert self.runtime._active_mission_id == m.id

    def test_activate_nonexistent(self):
        with self.assertRaises(ValueError):
            self.runtime.activate_mission("nope")

    def test_pause_mission(self):
        m = self.runtime.create_mission("m")
        self.runtime.activate_mission(m.id)
        m = self.runtime.pause_mission(m.id)
        assert m.status.value == "paused"
        assert self.runtime._active_mission_id is None

    def test_resume_mission(self):
        m = self.runtime.create_mission("m")
        self.runtime.activate_mission(m.id)
        self.runtime.pause_mission(m.id)
        m = self.runtime.resume_mission(m.id)
        assert m.status.value == "active"

    def test_complete_mission(self):
        m = self.runtime.create_mission("m")
        self.runtime.activate_mission(m.id)
        m = self.runtime.complete_mission(m.id)
        assert m.status.value == "completed"

    def test_fail_mission(self):
        m = self.runtime.create_mission("m")
        self.runtime.activate_mission(m.id)
        m = self.runtime.fail_mission(m.id, "reason")
        assert m.status.value == "failed"

    def test_cancel_mission(self):
        m = self.runtime.create_mission("m")
        m = self.runtime.cancel_mission(m.id)
        assert m.status.value == "cancelled"

    def test_add_goal(self):
        m = self.runtime.create_mission("m")
        g = self.runtime.add_goal(m.id, "root goal")
        assert g.name == "root goal"
        tree = self.runtime.get_goal_tree(m.id)
        assert tree.count() == 1

    def test_add_child_goal(self):
        m = self.runtime.create_mission("m")
        root = self.runtime.add_goal(m.id, "root")
        child = self.runtime.add_goal(m.id, "child", parent_id=root.id)
        tree = self.runtime.get_goal_tree(m.id)
        children = tree.get_children(root.id)
        assert len(children) == 1

    def test_complete_goal(self):
        m = self.runtime.create_mission("m")
        g = self.runtime.add_goal(m.id, "g")
        assert self.runtime.complete_goal(m.id, g.id)
        tree = self.runtime.get_goal_tree(m.id)
        assert tree.get_goal(g.id).status == "completed"

    def test_goal_completion(self):
        m = self.runtime.create_mission("m")
        root = self.runtime.add_goal(m.id, "root")
        c1 = self.runtime.add_goal(m.id, "c1", parent_id=root.id)
        c2 = self.runtime.add_goal(m.id, "c2", parent_id=root.id)
        self.runtime.complete_goal(m.id, c1.id)
        ratio = self.runtime.get_goal_completion(m.id)
        assert abs(ratio - 0.5) < 0.01

    def test_add_task(self):
        m = self.runtime.create_mission("m")
        t = self.runtime.add_task(m.id, "task1", action="do_it")
        assert t.name == "task1"
        graph = self.runtime.get_task_graph(m.id)
        assert graph.count() == 1

    def test_add_task_with_goal(self):
        m = self.runtime.create_mission("m")
        g = self.runtime.add_goal(m.id, "g")
        t = self.runtime.add_task(m.id, "t", goal_id=g.id)
        tree = self.runtime.get_goal_tree(m.id)
        assert t.id in tree.get_goal(g.id).task_ids

    def test_start_task(self):
        m = self.runtime.create_mission("m")
        t = self.runtime.add_task(m.id, "t")
        assert self.runtime.start_task(m.id, t.id)

    def test_complete_task(self):
        m = self.runtime.create_mission("m")
        t = self.runtime.add_task(m.id, "t")
        assert self.runtime.complete_task(m.id, t.id, result="done")
        mission = self.runtime.get_mission(m.id)
        assert mission.context.completed_tasks == 1

    def test_fail_task(self):
        m = self.runtime.create_mission("m")
        t = self.runtime.add_task(m.id, "t")
        assert self.runtime.fail_task(m.id, t.id, error="bad")
        mission = self.runtime.get_mission(m.id)
        assert mission.context.failed_tasks == 1

    def test_get_ready_tasks(self):
        m = self.runtime.create_mission("m")
        t1 = self.runtime.add_task(m.id, "t1")
        t2 = self.runtime.add_task(m.id, "t2", dependencies=[t1.id])
        ready = self.runtime.get_ready_tasks(m.id)
        assert len(ready) == 1

    def test_next_action(self):
        m = self.runtime.create_mission("m")
        t1 = self.runtime.add_task(m.id, "t1")
        t2 = self.runtime.add_task(m.id, "t2", dependencies=[t1.id])
        nxt = self.runtime.next_action(m.id)
        assert nxt.id == t1.id

    def test_next_action_empty(self):
        m = self.runtime.create_mission("m")
        assert self.runtime.next_action(m.id) is None

    def test_get_progress(self):
        m = self.runtime.create_mission("m")
        self.runtime.add_task(m.id, "t1")
        self.runtime.add_task(m.id, "t2")
        self.runtime.complete_task(m.id, m.id)  # just to test the API
        # Note: we need actual task ids
        t1 = self.runtime.add_task(m.id, "t1_real")
        self.runtime.complete_task(m.id, t1.id)
        progress = self.runtime.get_progress(m.id)
        assert progress is not None
        assert "overall_progress" in progress
        assert "tasks" in progress

    def test_reflect(self):
        m = self.runtime.create_mission("m")
        self.runtime.add_goal(m.id, "g1")
        t = self.runtime.add_task(m.id, "t1")
        self.runtime.activate_mission(m.id)
        self.runtime.complete_task(m.id, t.id)
        reflection = self.runtime.reflect(m.id)
        assert "mission_id" in reflection
        assert "insights" in reflection
        assert "recommendations" in reflection

    def test_reflect_nonexistent(self):
        result = self.runtime.reflect("nope")
        assert "error" in result

    def test_get_reflections(self):
        m = self.runtime.create_mission("m")
        self.runtime.reflect(m.id)
        reflections = self.runtime.get_reflections(m.id)
        assert len(reflections) == 1

    def test_event_emission(self):
        received = []
        self.bus.subscribe("MissionCreated", lambda e: received.append(e))
        self.bus.subscribe("MissionUpdated", lambda e: received.append(e))
        m = self.runtime.create_mission("m")
        self.runtime.activate_mission(m.id)
        types = [e.event_type for e in received]
        assert "MissionCreated" in types
        assert "MissionUpdated" in types

    def test_task_events(self):
        received = []
        self.bus.subscribe("TaskCreated", lambda e: received.append(e))
        self.bus.subscribe("TaskStarted", lambda e: received.append(e))
        self.bus.subscribe("TaskCompleted", lambda e: received.append(e))
        m = self.runtime.create_mission("m")
        t = self.runtime.add_task(m.id, "t")
        self.runtime.start_task(m.id, t.id)
        self.runtime.complete_task(m.id, t.id)
        types = [e.event_type for e in received]
        assert "TaskCreated" in types
        assert "TaskStarted" in types
        assert "TaskCompleted" in types

    def test_goal_events(self):
        received = []
        self.bus.subscribe("GoalCreated", lambda e: received.append(e))
        self.bus.subscribe("GoalCompleted", lambda e: received.append(e))
        m = self.runtime.create_mission("m")
        g = self.runtime.add_goal(m.id, "g")
        self.runtime.complete_goal(m.id, g.id)
        types = [e.event_type for e in received]
        assert "GoalCreated" in types
        assert "GoalCompleted" in types

    def test_mission_finished_events(self):
        received = []
        self.bus.subscribe("MissionFinished", lambda e: received.append(e))
        m = self.runtime.create_mission("m")
        self.runtime.activate_mission(m.id)
        self.runtime.complete_mission(m.id)
        assert len(received) == 1
        assert received[0].payload["name"] == "m"

    def test_stats(self):
        self.runtime.create_mission("m1")
        self.runtime.create_mission("m2")
        stats = self.runtime.get_stats()
        assert stats["total_missions"] == 2
        assert stats["loaded"] is True

    def test_health_check(self):
        from prototype.diagnostics.diagnostics import Diagnostics
        diag = Diagnostics()
        runtime = self.runtime.__class__(
            event_bus=self.bus, diagnostics=diag,
        )
        runtime.load()
        status = diag.check_health("mission")
        assert status.healthy
        runtime.shutdown()

    def test_memory_integration(self):
        from prototype.memory.memory import Memory
        mem = Memory()
        mem.load()
        runtime = self.runtime.__class__(memory_manager=mem)
        runtime.load()
        m = runtime.create_mission("m")
        runtime.activate_mission(m.id)
        runtime.complete_mission(m.id)
        # Should have stored a memory
        episodes = mem.recall("mission")
        assert len(episodes) > 0
        runtime.shutdown()

    def test_full_lifecycle(self):
        """End-to-end: create → goals → tasks → activate → execute → complete."""
        m = self.runtime.create_mission("Build feature", description="Full feature build")
        g1 = self.runtime.add_goal(m.id, "Design")
        g2 = self.runtime.add_goal(m.id, "Implement")
        g3 = self.runtime.add_goal(m.id, "Test")

        t1 = self.runtime.add_task(m.id, "Design system", goal_id=g1.id)
        t2 = self.runtime.add_task(m.id, "Write code", dependencies=[t1.id], goal_id=g2.id)
        t3 = self.runtime.add_task(m.id, "Run tests", dependencies=[t2.id], goal_id=g3.id)

        self.runtime.activate_mission(m.id)

        # Execute tasks in order
        self.runtime.start_task(m.id, t1.id)
        self.runtime.complete_task(m.id, t1.id)
        self.runtime.complete_goal(m.id, g1.id)

        ready = self.runtime.get_ready_tasks(m.id)
        assert len(ready) == 1
        assert ready[0].id == t2.id

        self.runtime.start_task(m.id, t2.id)
        self.runtime.complete_task(m.id, t2.id)
        self.runtime.complete_goal(m.id, g2.id)

        self.runtime.start_task(m.id, t3.id)
        self.runtime.complete_task(m.id, t3.id)
        self.runtime.complete_goal(m.id, g3.id)

        progress = self.runtime.get_progress(m.id)
        assert progress["overall_progress"] >= 0.9

        reflection = self.runtime.reflect(m.id)
        assert len(reflection["insights"]) > 0

        self.runtime.complete_mission(m.id)
        assert m.status.value == "completed"


# ═══════════════════════════════════════════════════════════════════════════════
#  Integration with existing ALFA components
# ═══════════════════════════════════════════════════════════════════════════════

class TestMissionIntegration(unittest.TestCase):
    def test_event_bus_wiring(self):
        from prototype.mission.mission_runtime import MissionRuntime
        bus = EventBus()
        runtime = MissionRuntime(event_bus=bus)

        events = []
        bus.subscribe("*", lambda e: events.append(e.event_type))

        runtime.load()
        m = runtime.create_mission("m")
        runtime.activate_mission(m.id)
        runtime.shutdown()

        assert "MissionCreated" in events
        assert "MissionUpdated" in events
        assert "MissionRuntimeStarted" in events
        assert "MissionRuntimeShutdown" in events

    def test_diagnostics_wiring(self):
        from prototype.mission.mission_runtime import MissionRuntime
        from prototype.diagnostics.diagnostics import Diagnostics
        bus = EventBus()
        diag = Diagnostics()
        runtime = MissionRuntime(event_bus=bus, diagnostics=diag)
        runtime.load()

        m = runtime.create_mission("m")
        runtime.activate_mission(m.id)
        runtime.complete_mission(m.id)

        assert diag.get_counter("mission.created_count") >= 1
        assert diag.get_counter("mission.activation_count") >= 1
        assert diag.get_counter("mission.completed_count") >= 1

        runtime.shutdown()


if __name__ == "__main__":
    unittest.main()
