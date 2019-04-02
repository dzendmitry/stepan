.PHONY: build-service
build-service:
	docker build -t stepan-service:master .

.PHONY: run-service
run-service:
	docker run -p 5006:5006/udp -p 8080:8080 stepan-service:master

.PHONY: build-microphone
build-microphone:
	docker build -t stepan-microphone:master microphone

.PHONY: run-microphone
run-microphone:
	docker run stepan-microphone:master
