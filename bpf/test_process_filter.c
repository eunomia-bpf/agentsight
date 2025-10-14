#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>

// Include Linux types if available, otherwise define our own
#ifdef __linux__
#include <linux/types.h>
#else
// BPF type definitions for testing
typedef uint32_t __u32;
typedef uint64_t __u64;
#endif

#ifndef BPF_ANY
#define BPF_ANY 0
#endif

#include "process.h"
#include "process_filter.h"

// Test colors for output
#define RESET   "\033[0m"
#define RED     "\033[31m"
#define GREEN   "\033[32m"
#define YELLOW  "\033[33m"
#define BLUE    "\033[34m"

static int tests_passed = 0;
static int tests_failed = 0;

void test_assert(bool condition, const char *test_name) {
    if (condition) {
        printf("[" GREEN "PASS" RESET "] %s\n", test_name);
        tests_passed++;
    } else {
        printf("[" RED "FAIL" RESET "] %s\n", test_name);
        tests_failed++;
    }
}

void test_pid_hash() {
    printf("\n" BLUE "Testing pid_hash function:" RESET "\n");

    // Test basic hash function
    unsigned int hash1 = pid_hash(1234);
    unsigned int hash2 = pid_hash(5678);
    unsigned int hash3 = pid_hash(1234); // Same as hash1

    test_assert(hash1 < TRACKED_PIDS_HASH_SIZE, "hash should be within bounds");
    test_assert(hash2 < TRACKED_PIDS_HASH_SIZE, "hash should be within bounds");
    test_assert(hash1 == hash3, "same PID should produce same hash");

    printf("  hash(1234) = %u\n", hash1);
    printf("  hash(5678) = %u\n", hash2);
}

void test_pid_tracker_init() {
    printf("\n" BLUE "Testing pid_tracker_init function:" RESET "\n");

    struct pid_tracker tracker;
    char *filters[] = {"bash", "python"};
    int filter_count = 2;

    pid_tracker_init(&tracker, filters, filter_count, FILTER_MODE_FILTER, 1234);

    test_assert(tracker.command_filters == filters, "command_filters should be set");
    test_assert(tracker.command_filter_count == 2, "command_filter_count should be 2");
    test_assert(tracker.filter_mode == FILTER_MODE_FILTER, "filter_mode should be FILTER");
    test_assert(tracker.target_pid == 1234, "target_pid should be 1234");

    // Check that all entries are inactive
    bool all_inactive = true;
    for (int i = 0; i < TRACKED_PIDS_HASH_SIZE; i++) {
        if (tracker.entries[i].is_active) {
            all_inactive = false;
            break;
        }
    }
    test_assert(all_inactive, "all entries should be inactive after init");
}

void test_pid_tracker_add_and_find() {
    printf("\n" BLUE "Testing pid_tracker_add and pid_tracker_find functions:" RESET "\n");

    struct pid_tracker tracker;
    pid_tracker_init(&tracker, NULL, 0, FILTER_MODE_ALL, 0);

    // Test adding PIDs
    bool result1 = pid_tracker_add(&tracker, 1234, 1000);
    test_assert(result1, "should successfully add PID 1234");

    bool result2 = pid_tracker_add(&tracker, 5678, 1000);
    test_assert(result2, "should successfully add PID 5678");

    // Test finding PIDs
    struct tracked_pid_entry *entry1 = pid_tracker_find(&tracker, 1234);
    test_assert(entry1 != NULL, "should find PID 1234");
    test_assert(entry1->pid == 1234, "found entry should have correct PID");
    test_assert(entry1->ppid == 1000, "found entry should have correct PPID");
    test_assert(entry1->is_tracked, "found entry should be tracked");
    test_assert(entry1->is_active, "found entry should be active");

    struct tracked_pid_entry *entry2 = pid_tracker_find(&tracker, 5678);
    test_assert(entry2 != NULL, "should find PID 5678");

    // Test finding non-existent PID
    struct tracked_pid_entry *entry3 = pid_tracker_find(&tracker, 9999);
    test_assert(entry3 == NULL, "should not find non-existent PID 9999");

    // Test adding duplicate PID
    bool result3 = pid_tracker_add(&tracker, 1234, 1000);
    test_assert(result3, "adding duplicate should return true");
}

void test_pid_tracker_remove() {
    printf("\n" BLUE "Testing pid_tracker_remove function:" RESET "\n");

    struct pid_tracker tracker;
    pid_tracker_init(&tracker, NULL, 0, FILTER_MODE_ALL, 0);

    // Add and then remove a PID
    pid_tracker_add(&tracker, 1234, 1000);

    struct tracked_pid_entry *entry1 = pid_tracker_find(&tracker, 1234);
    test_assert(entry1 != NULL, "should find PID before removal");

    pid_tracker_remove(&tracker, 1234);

    struct tracked_pid_entry *entry2 = pid_tracker_find(&tracker, 1234);
    test_assert(entry2 == NULL, "should not find PID after removal");

    // Test removing non-existent PID (should not crash)
    pid_tracker_remove(&tracker, 9999);
    test_assert(true, "removing non-existent PID should not crash");
}

void test_pid_tracker_is_tracked() {
    printf("\n" BLUE "Testing pid_tracker_is_tracked function:" RESET "\n");

    struct pid_tracker tracker;
    pid_tracker_init(&tracker, NULL, 0, FILTER_MODE_ALL, 0);

    // Test with tracked PID
    pid_tracker_add(&tracker, 1234, 1000);
    test_assert(pid_tracker_is_tracked(&tracker, 1234), "tracked PID should return true");

    // Test with non-tracked PID
    test_assert(!pid_tracker_is_tracked(&tracker, 9999), "non-tracked PID should return false");
}

void test_command_matches_any_filter() {
    printf("\n" BLUE "Testing command_matches_any_filter function:" RESET "\n");

    char *filters[] = {"bash", "python", "node"};
    int filter_count = 3;

    // Test matching commands
    test_assert(command_matches_any_filter("bash", filters, filter_count),
                "bash should match");
    test_assert(command_matches_any_filter("python", filters, filter_count),
                "python should match");
    test_assert(command_matches_any_filter("node", filters, filter_count),
                "node should match");

    // Test non-matching commands
    test_assert(!command_matches_any_filter("vim", filters, filter_count),
                "vim should not match");
    test_assert(!command_matches_any_filter("emacs", filters, filter_count),
                "emacs should not match");

    // Test with empty filter list
    test_assert(!command_matches_any_filter("bash", NULL, 0),
                "empty filter list should not match");
}

void test_should_track_process_all_mode() {
    printf("\n" BLUE "Testing should_track_process with FILTER_MODE_ALL:" RESET "\n");

    struct pid_tracker tracker;
    char *filters[] = {"bash"};
    pid_tracker_init(&tracker, filters, 1, FILTER_MODE_ALL, 0);

    // In ALL mode, everything should be tracked
    test_assert(should_track_process(&tracker, "bash", 1234, 1000),
                "bash should be tracked in ALL mode");
    test_assert(should_track_process(&tracker, "python", 5678, 1000),
                "python should be tracked in ALL mode");
    test_assert(should_track_process(&tracker, "vim", 9999, 1000),
                "vim should be tracked in ALL mode");
}

void test_should_track_process_proc_mode() {
    printf("\n" BLUE "Testing should_track_process with FILTER_MODE_PROC:" RESET "\n");

    struct pid_tracker tracker;
    char *filters[] = {"bash"};
    pid_tracker_init(&tracker, filters, 1, FILTER_MODE_PROC, 0);

    // In PROC mode, all processes should be tracked
    test_assert(should_track_process(&tracker, "bash", 1234, 1000),
                "bash should be tracked in PROC mode");
    test_assert(should_track_process(&tracker, "python", 5678, 1000),
                "python should be tracked in PROC mode");
}

void test_should_track_process_filter_mode() {
    printf("\n" BLUE "Testing should_track_process with FILTER_MODE_FILTER:" RESET "\n");

    struct pid_tracker tracker;
    char *filters[] = {"bash", "python"};
    pid_tracker_init(&tracker, filters, 2, FILTER_MODE_FILTER, 0);

    // Test command matching
    test_assert(should_track_process(&tracker, "bash", 1234, 1000),
                "bash should be tracked (matches filter)");
    test_assert(should_track_process(&tracker, "python", 5678, 1000),
                "python should be tracked (matches filter)");
    test_assert(!should_track_process(&tracker, "vim", 9999, 1000),
                "vim should not be tracked (no match)");

    // Test parent tracking
    pid_tracker_add(&tracker, 1234, 1000);
    test_assert(should_track_process(&tracker, "vim", 2000, 1234),
                "child of tracked parent should be tracked");
    test_assert(!should_track_process(&tracker, "emacs", 3000, 5555),
                "child of non-tracked parent should not be tracked");
}

void test_should_track_process_target_pid() {
    printf("\n" BLUE "Testing should_track_process with target PID:" RESET "\n");

    struct pid_tracker tracker;
    pid_tracker_init(&tracker, NULL, 0, FILTER_MODE_FILTER, 1234);

    // Target PID should be tracked
    test_assert(should_track_process(&tracker, "bash", 1234, 1000),
                "target PID should be tracked");
    test_assert(!should_track_process(&tracker, "bash", 5678, 1000),
                "non-target PID should not be tracked");
}

void test_should_report_file_ops() {
    printf("\n" BLUE "Testing should_report_file_ops function:" RESET "\n");

    struct pid_tracker tracker;
    char *filters[] = {"bash"};

    // Test FILTER_MODE_ALL
    pid_tracker_init(&tracker, filters, 1, FILTER_MODE_ALL, 0);
    test_assert(should_report_file_ops(&tracker, 1234),
                "ALL mode should report all file ops");

    // Test FILTER_MODE_PROC with tracked PID
    pid_tracker_init(&tracker, filters, 1, FILTER_MODE_PROC, 0);
    pid_tracker_add(&tracker, 1234, 1000);
    test_assert(should_report_file_ops(&tracker, 1234),
                "PROC mode should report tracked PID file ops");
    test_assert(!should_report_file_ops(&tracker, 5678),
                "PROC mode should not report non-tracked PID file ops");

    // Test FILTER_MODE_FILTER with tracked PID
    pid_tracker_init(&tracker, filters, 1, FILTER_MODE_FILTER, 0);
    pid_tracker_add(&tracker, 1234, 1000);
    test_assert(should_report_file_ops(&tracker, 1234),
                "FILTER mode should report tracked PID file ops");
    test_assert(!should_report_file_ops(&tracker, 5678),
                "FILTER mode should not report non-tracked PID file ops");
}

void test_should_report_bash_readline() {
    printf("\n" BLUE "Testing should_report_bash_readline function:" RESET "\n");

    struct pid_tracker tracker;
    char *filters[] = {"bash"};

    // Test FILTER_MODE_ALL
    pid_tracker_init(&tracker, filters, 1, FILTER_MODE_ALL, 0);
    test_assert(should_report_bash_readline(&tracker, 1234),
                "ALL mode should report all bash readline");

    // Test FILTER_MODE_PROC
    pid_tracker_init(&tracker, filters, 1, FILTER_MODE_PROC, 0);
    test_assert(should_report_bash_readline(&tracker, 1234),
                "PROC mode should report all bash readline");

    // Test FILTER_MODE_FILTER with tracked PID
    pid_tracker_init(&tracker, filters, 1, FILTER_MODE_FILTER, 0);
    pid_tracker_add(&tracker, 1234, 1000);
    test_assert(should_report_bash_readline(&tracker, 1234),
                "FILTER mode should report tracked PID bash readline");
    test_assert(!should_report_bash_readline(&tracker, 5678),
                "FILTER mode should not report non-tracked PID bash readline");
}

void test_hash_collision_handling() {
    printf("\n" BLUE "Testing hash collision handling:" RESET "\n");

    struct pid_tracker tracker;
    pid_tracker_init(&tracker, NULL, 0, FILTER_MODE_ALL, 0);

    // Add PIDs until we might hit collisions
    int added_count = 0;
    for (int i = 1; i <= 100; i++) {
        if (pid_tracker_add(&tracker, i, i - 1)) {
            added_count++;
        }
    }

    test_assert(added_count == 100, "should handle multiple PIDs without issues");

    // Verify all PIDs can be found
    int found_count = 0;
    for (int i = 1; i <= 100; i++) {
        if (pid_tracker_find(&tracker, i) != NULL) {
            found_count++;
        }
    }

    test_assert(found_count == 100, "should find all added PIDs");
    printf("  Added and found %d PIDs successfully\n", found_count);
}

void test_integration_scenario() {
    printf("\n" BLUE "Testing integration scenario:" RESET "\n");

    struct pid_tracker tracker;
    char *filters[] = {"bash", "python"};
    pid_tracker_init(&tracker, filters, 2, FILTER_MODE_FILTER, 0);

    // Simulate process lifecycle
    pid_t bash_pid = 1000;
    pid_t python_pid = 2000;
    pid_t child_pid = 3000;

    // 1. bash starts - should be tracked
    test_assert(should_track_process(&tracker, "bash", bash_pid, 1),
                "bash process should be tracked");
    pid_tracker_add(&tracker, bash_pid, 1);

    // 2. python starts - should be tracked
    test_assert(should_track_process(&tracker, "python", python_pid, 1),
                "python process should be tracked");
    pid_tracker_add(&tracker, python_pid, 1);

    // 3. bash spawns child - child should be tracked
    test_assert(should_track_process(&tracker, "ls", child_pid, bash_pid),
                "child of bash should be tracked");
    pid_tracker_add(&tracker, child_pid, bash_pid);

    // 4. Check file ops reporting
    test_assert(should_report_file_ops(&tracker, bash_pid),
                "bash file ops should be reported");
    test_assert(should_report_file_ops(&tracker, child_pid),
                "child file ops should be reported");
    test_assert(!should_report_file_ops(&tracker, 9999),
                "random PID file ops should not be reported");

    // 5. Process exits
    pid_tracker_remove(&tracker, child_pid);
    test_assert(!pid_tracker_is_tracked(&tracker, child_pid),
                "child should be removed after exit");
    test_assert(pid_tracker_is_tracked(&tracker, bash_pid),
                "bash should still be tracked");

    printf("  Integration scenario completed successfully\n");
}

void print_test_summary() {
    printf("\n" YELLOW "===== Test Summary =====" RESET "\n");
    printf("Tests passed: " GREEN "%d" RESET "\n", tests_passed);
    printf("Tests failed: " RED "%d" RESET "\n", tests_failed);
    printf("Total tests:  %d\n", tests_passed + tests_failed);

    if (tests_failed == 0) {
        printf(GREEN "All tests passed!" RESET "\n");
    } else {
        printf(RED "Some tests failed!" RESET "\n");
    }
}

int main() {
    printf(BLUE "===== Process Filter Test Suite =====" RESET "\n");
    printf("Testing functions from process_filter.h\n");

    test_pid_hash();
    test_pid_tracker_init();
    test_pid_tracker_add_and_find();
    test_pid_tracker_remove();
    test_pid_tracker_is_tracked();
    test_command_matches_any_filter();
    test_should_track_process_all_mode();
    test_should_track_process_proc_mode();
    test_should_track_process_filter_mode();
    test_should_track_process_target_pid();
    test_should_report_file_ops();
    test_should_report_bash_readline();
    test_hash_collision_handling();
    test_integration_scenario();

    print_test_summary();

    return (tests_failed > 0) ? 1 : 0;
}
