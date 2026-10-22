# Lab 4, Part B, step 3: write the recipe of the image here.
#
# TODO, in this order (the order matters for the layer cache):
#   1. Start from the official Python image, pinned: python:3.12-slim
#   2. Choose a working directory (for example /srv)
#   3. Copy ONLY app/requirements.txt, then install it with pip
#   4. Copy the code (the app/ folder)
#   5. Create a user that is not root, and switch to it
#   6. Say which port the service listens on (8000), and how to start it:
#        python -m app.main
#
# Never write a password, a key or a DATABASE_URL in this file:
# everything you write here ends up inside the image, readable by anyone who has it.
