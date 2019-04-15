.PHONY: build-service
build-service:
	docker build -t stepan-service:latest .

.PHONY: run-service
run-service:
	docker run -p 5006:5006/udp -p 8080:8080 stepan-service:latest
