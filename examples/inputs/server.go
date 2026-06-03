package main

import (
	"encoding/json"
	"log"
	"net/http"
)

type response struct {
	Status string `json:"status"`
	Count  int    `json:"count"`
}

func health(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response{Status: "ok", Count: 3})
}

func main() {
	http.HandleFunc("/health", health)
	log.Fatal(http.ListenAndServe(":8080", nil))
}
