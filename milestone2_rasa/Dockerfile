# Use the official Rasa SDK image
FROM rasa/rasa-sdk:3.6.2

# Switch to root user to install extra packages
USER root

# Install database libraries required by your actions.py
RUN pip install --no-cache-dir sqlalchemy pandas

# Switch back to non-root user for security
USER 1001