---
Agent.md file for coding spec in this repository
---

- Always import at the top-level
- Alway check your work using ruff format ./, ruff check ./ and pytest -vv
- Zvec doesn't install on darwin x86_64, so first check if docker is active (docker ps | grep 'jovial_keldysh') before running the test specified in Makefile (docker-test).
- Always ask me to install dependencies for you. This is because Zvec would cause uv pip... to fail on my local machine which is why we have a linux docker container.
