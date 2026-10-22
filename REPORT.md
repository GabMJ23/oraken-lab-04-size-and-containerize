# Lab 4 report

Replace every `TODO` with your answer. The automated checks make sure nothing is left blank.

## Part A: Size the service

One copy of the agent handles 4 questions at a time. Show the formula with the numbers, not only the result.

**A1.** Case 1: 6 questions per minute, 40 seconds each.

- Questions in progress on average, L = λ × W: TODO
- Copies needed without margin: TODO
- Copies needed with a 25% margin: TODO

**A2.** Case 2: 30 questions per minute, 90 seconds each.

- L: TODO
- Copies without margin: TODO
- Copies with a 25% margin: TODO

**A3.** Case 3: case 2 on a day the model provider slows down, and each analysis takes 180 seconds.

- L: TODO
- Copies without margin: TODO
- Copies with a 25% margin: TODO
- Where is the bottleneck on that day? Does adding copies solve the problem? Explain in two or three sentences.

TODO

**A4.** With the simple queue model, wait = ρ / (1 − ρ) × task duration, what is the average wait in case 1:

- with one copy (give ρ, then the wait, and say what happens to the queue): TODO
- with two copies (give ρ, then the wait): TODO

## Part B: Containerize the service

**B1.** Paste the output of `docker run --rm --entrypoint id lab04-search -u`. Why does it matter that it is not `0`?

TODO

**B2.** Run `docker compose up --build` once and note how long the build takes. Then change one line of code (the `VERSION` line in `app/main.py`) and rebuild. How long does the second build take? Why is it so much shorter?

- First build: TODO
- Rebuild after changing one line: TODO
- Why so short: TODO

**B3.** In `docker-compose.yml`, the host in `DATABASE_URL` is the name of the database service, not `localhost`. Why?

TODO

**B4.** What does your `.dockerignore` keep out of the image? What would happen if your `.env` ended up inside the image?

TODO

**Going further (optional).** The model provider lets you run at most 60 analyses at the same time. On the slow day of case 3 (180 s per analysis), how many questions per minute can you serve at most, however many copies you start? What is the size of your image (`docker images lab04-search`)?

TODO
