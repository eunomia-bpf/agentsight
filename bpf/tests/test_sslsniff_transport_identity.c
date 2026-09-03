// SPDX-License-Identifier: MIT

#define _GNU_SOURCE
#include <pthread.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/syscall.h>
#include <unistd.h>

#define EXPORTED_NOINLINE __attribute__((noinline, visibility("default")))
#define CAPTURE_LIMIT (256 * 1024)
#define TRUNCATED_PAYLOAD_SIZE (CAPTURE_LIMIT + 17)

struct fake_ssl {
	unsigned int id;
};

static struct fake_ssl handle_a = { .id = 1 };
static struct fake_ssl handle_b = { .id = 2 };
static _Thread_local const char *pending_read_payload;
static char truncated_payload[TRUNCATED_PAYLOAD_SIZE + 1];
static _Atomic int result_sink;
static pthread_barrier_t worker_barrier;

struct worker_result {
	long tid;
};

EXPORTED_NOINLINE int SSL_write(void *ssl, const void *buf, int num)
{
	(void)ssl;
	if (!buf || num <= 0)
		return 0;
	atomic_fetch_add_explicit(&result_sink, ((const unsigned char *)buf)[0],
				  memory_order_relaxed);
	return num;
}

EXPORTED_NOINLINE int SSL_read(void *ssl, void *buf, int num)
{
	size_t len;

	(void)ssl;
	if (!pending_read_payload || !buf || num <= 0)
		return 0;
	len = strlen(pending_read_payload);
	if (len > (size_t)num)
		len = (size_t)num;
	memcpy(buf, pending_read_payload, len);
	atomic_fetch_add_explicit(&result_sink, ((const unsigned char *)buf)[0],
				  memory_order_relaxed);
	return (int)len;
}

EXPORTED_NOINLINE int SSL_write_ex(void *ssl, const void *buf, size_t num,
					  size_t *written)
{
	(void)ssl;
	(void)buf;
	if (written)
		*written = num;
	return 1;
}

EXPORTED_NOINLINE int SSL_read_ex(void *ssl, void *buf, size_t num,
					 size_t *readbytes)
{
	(void)ssl;
	(void)buf;
	(void)num;
	if (readbytes)
		*readbytes = 0;
	return 1;
}

EXPORTED_NOINLINE int SSL_do_handshake(void *ssl)
{
	(void)ssl;
	atomic_fetch_add_explicit(&result_sink, 1, memory_order_relaxed);
	return 1;
}

EXPORTED_NOINLINE void SSL_free(void *ssl)
{
	(void)ssl;
	atomic_fetch_add_explicit(&result_sink, 1, memory_order_relaxed);
}

static void write_marker(void *handle, const char *marker)
{
	int len = (int)strlen(marker);

	if (SSL_write(handle, marker, len) != len) {
		fprintf(stderr, "SSL_write fixture call failed\n");
		exit(2);
	}
}

static void *write_worker(void *arg)
{
	struct worker_result *result = arg;
	const char marker[] = "identity-thread-write-a";

	result->tid = syscall(SYS_gettid);
	pthread_barrier_wait(&worker_barrier);
	write_marker(&handle_a, marker);
	return NULL;
}

static void *read_worker(void *arg)
{
	struct worker_result *result = arg;
	char buf[64] = {};
	const char marker[] = "identity-thread-read-a";

	result->tid = syscall(SYS_gettid);
	pending_read_payload = marker;
	pthread_barrier_wait(&worker_barrier);
	if (SSL_read(&handle_a, buf, sizeof(buf)) != (int)strlen(marker)) {
		fprintf(stderr, "SSL_read fixture call failed\n");
		exit(3);
	}
	return NULL;
}

int main(void)
{
	pthread_t write_thread;
	pthread_t read_thread;
	struct worker_result write_result = {};
	struct worker_result read_result = {};
	char trigger;
	long main_tid = syscall(SYS_gettid);

	setvbuf(stdout, NULL, _IONBF, 0);
	printf("READY pid=%ld main_tid=%ld handle_a=%p handle_b=%p\n",
	       (long)getpid(), main_tid, (void *)&handle_a, (void *)&handle_b);
	if (read(STDIN_FILENO, &trigger, 1) != 1) {
		fprintf(stderr, "fixture did not receive trigger\n");
		return 1;
	}

	/* Required case 1: one TID alternates between two TLS handles. */
	write_marker(&handle_a, "identity-main-a-1");
	write_marker(&handle_b, "identity-main-b-1");
	write_marker(&handle_a, "identity-main-a-2");
	write_marker(&handle_b, "identity-main-b-2");

	memset(truncated_payload, 'x', TRUNCATED_PAYLOAD_SIZE);
	memcpy(truncated_payload, "identity-truncated-a", 20);
	truncated_payload[TRUNCATED_PAYLOAD_SIZE] = '\0';
	write_marker(&handle_a, truncated_payload);

	/* Required case 2: the same TLS handle is used by different TIDs. */
	if (pthread_barrier_init(&worker_barrier, NULL, 3) != 0)
		return 4;
	if (pthread_create(&write_thread, NULL, write_worker, &write_result) != 0)
		return 5;
	if (pthread_create(&read_thread, NULL, read_worker, &read_result) != 0)
		return 6;
	pthread_barrier_wait(&worker_barrier);
	pthread_join(write_thread, NULL);
	pthread_join(read_thread, NULL);
	pthread_barrier_destroy(&worker_barrier);

	SSL_do_handshake(&handle_a);
	SSL_free(&handle_a);
	SSL_free(&handle_b);

	printf("THREADS write_tid=%ld read_tid=%ld\n",
	       write_result.tid, read_result.tid);
	printf("DONE sink=%d\n",
	       atomic_load_explicit(&result_sink, memory_order_relaxed));
	return write_result.tid == read_result.tid;
}
