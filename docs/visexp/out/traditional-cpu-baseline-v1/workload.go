// A small but realistic Go HTTP service, profiled with stock runtime/pprof.
// Used only to produce a conventional CPU profile for the paper's
// traditional-versus-semantic flame graph comparison.
package main

import (
	"bytes"
	"crypto/sha256"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/http/httptest"
	"os"
	"runtime/pprof"
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"
)

type record struct {
	id   int
	name string
	tags []string
}

func parseRequest(body []byte) []record {
	lines := strings.Split(string(body), "\n")
	recs := make([]record, 0, len(lines))
	for _, line := range lines {
		if line == "" {
			continue
		}
		parts := strings.Split(line, "|")
		if len(parts) < 3 {
			continue
		}
		id, err := strconv.Atoi(parts[0])
		if err != nil {
			continue
		}
		recs = append(recs, record{id: id, name: parts[1], tags: strings.Split(parts[2], ",")})
	}
	return recs
}

func validate(recs []record) int {
	n := 0
	for _, r := range recs {
		for _, t := range r.tags {
			if strings.HasPrefix(t, "prod") && strings.ContainsAny(t, "0123456789") {
				n++
			}
		}
	}
	return n
}

func digest(recs []record) string {
	h := sha256.New()
	buf := make([]byte, 0, 64)
	for _, r := range recs {
		buf = append(buf[:0], r.name...)
		buf = strconv.AppendInt(buf, int64(r.id), 10)
		h.Write(buf)
		for _, t := range r.tags {
			io.WriteString(h, t)
		}
	}
	return fmt.Sprintf("%x", h.Sum(nil))
}

func rank(recs []record) []record {
	out := make([]record, len(recs))
	copy(out, recs)
	sort.Slice(out, func(i, j int) bool {
		if len(out[i].tags) != len(out[j].tags) {
			return len(out[i].tags) > len(out[j].tags)
		}
		return out[i].name < out[j].name
	})
	return out
}

func render(recs []record) []byte {
	var buf bytes.Buffer
	for _, r := range recs {
		buf.WriteString(r.name)
		buf.WriteByte('=')
		buf.WriteString(strconv.Itoa(len(r.tags)))
		buf.WriteByte(';')
	}
	return buf.Bytes()
}

func handleIngest(w http.ResponseWriter, req *http.Request) {
	body, err := io.ReadAll(req.Body)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	recs := parseRequest(body)
	ok := validate(recs)
	sum := digest(recs)
	payload := render(rank(recs))
	w.Header().Set("Content-Type", "text/plain")
	fmt.Fprintf(w, "accepted=%d digest=%s bytes=%d", ok, sum, len(payload))
}

func sampleBody(n int) []byte {
	var buf bytes.Buffer
	for i := 0; i < n; i++ {
		fmt.Fprintf(&buf, "%d|service-%03d|prod%02d,shard%02d,%s\n",
			i, i%97, i%42, i%13, strings.Repeat("x", i%7+1))
	}
	return buf.Bytes()
}

func main() {
	out, err := os.Create(os.Args[1])
	if err != nil {
		log.Fatal(err)
	}
	defer out.Close()

	mux := http.NewServeMux()
	mux.HandleFunc("/ingest", handleIngest)
	srv := httptest.NewServer(mux)
	defer srv.Close()

	body := sampleBody(400)
	if err := pprof.StartCPUProfile(out); err != nil {
		log.Fatal(err)
	}
	deadline := time.Now().Add(12 * time.Second)
	var wg sync.WaitGroup
	for w := 0; w < 8; w++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			client := &http.Client{}
			for time.Now().Before(deadline) {
				resp, err := client.Post(srv.URL+"/ingest", "text/plain", bytes.NewReader(body))
				if err != nil {
					return
				}
				io.Copy(io.Discard, resp.Body)
				resp.Body.Close()
			}
		}()
	}
	wg.Wait()
	pprof.StopCPUProfile()
	fmt.Println("wrote", os.Args[1])
}
