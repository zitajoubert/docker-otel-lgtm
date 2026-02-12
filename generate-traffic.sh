#!/bin/bash

watch 'curl -s http://127.0.0.1:8000/rolldice; \
  curl -s http://127.0.0.1:8000/rolldice; \
  curl -s http://127.0.0.1:8000/rolldice; \
  curl -s http://127.0.0.1:8000/rolldice; \
  curl -s http://127.0.0.1:8000/rolldice?rolls=5'
