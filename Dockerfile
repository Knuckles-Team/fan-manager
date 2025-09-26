FROM python:3-slim

# ARG FOR FAN MANAGER
ARG INTENSITY=5
ARG COLD=50
ARG WARM=80
ARG SLOW=5
ARG FAST=100
ARG POLL_RATE=24
# ARG FOR MCP
ARG HOST=0.0.0.0
ARG PORT=8030
ARG TRANSPORT="http"

# ENV to determine which mode to run (fan-manager or fan-manager-mcp)
ENV MODE="fan-manager"
# ENV FOR FAN MANAGER
ENV INTENSITY=${INTENSITY}
ENV COLD=${COLD}
ENV WARM=${WARM}
ENV SLOW=${SLOW}
ENV FAST=${FAST}
ENV POLL_RATE=${POLL_RATE}
# ENV FOR MCP
ENV HOST=${HOST}
ENV PORT=${PORT}
ENV TRANSPORT=${TRANSPORT}


ENV PATH="/usr/local/bin:${PATH}"
RUN pip install uv \
    && uv pip install --system fan-manager

# Set ENTRYPOINT to handle both modes using a shell command
ENTRYPOINT ["/bin/sh", "-c", "if [ \"$MODE\" = \"fan-manager\" ]; then exec fan-manager --intensity \"$INTENSITY\" --cold \"$COLD\" --warm \"$WARM\" --slow \"$SLOW\" --fast \"$FAST\" --poll-rate \"$POLL_RATE\"; elif [ \"$MODE\" = \"fan-manager-mcp\" ]; then exec fan-manager-mcp --transport \"$TRANSPORT\" --host \"$HOST\" --port \"$PORT\"; else echo \"Error: MODE must be 'fan-manager' or 'fan-manager-mcp'\"; exit 1; fi"]
