import datetime
import json
from dataclasses import dataclass
from typing import Dict, TypedDict

import grpc
from google.protobuf import timestamp_pb2

from ..events_pb2 import PushEventRequest, PutLogRequest, PutStreamEventRequest
from ..events_pb2_grpc import EventsServiceStub
from ..loader import ClientConfig
from ..metadata import get_metadata


def new_event(conn, config: ClientConfig):
    return EventClientImpl(
        client=EventsServiceStub(conn),
        config=config,
    )


def proto_timestamp_now():
    t = datetime.datetime.now().timestamp()
    seconds = int(t)
    nanos = int(t % 1 * 1e9)

    return timestamp_pb2.Timestamp(seconds=seconds, nanos=nanos)


class PushEventOptions(TypedDict):
    additional_metadata: Dict[str, str] | None = None


class EventClientImpl:
    def __init__(self, client: EventsServiceStub, config: ClientConfig):
        self.client = client
        self.token = config.token
        self.namespace = config.namespace

    def push(self, event_key, payload, options: PushEventOptions = None):

        namespaced_event_key = self.namespace + event_key

        try:
            meta = None if options is None else options["additional_metadata"]
            meta_bytes = None if meta is None else json.dumps(meta).encode("utf-8")
        except e:
            raise ValueError(f"Error encoding meta: {e}")

        try:
            payload_bytes = json.dumps(payload).encode("utf-8")
        except json.UnicodeEncodeError as e:
            raise ValueError(f"Error encoding payload: {e}")

        request = PushEventRequest(
            key=namespaced_event_key,
            payload=payload_bytes,
            eventTimestamp=proto_timestamp_now(),
            additionalMetadata=meta_bytes,
        )

        try:
            self.client.Push(request, metadata=get_metadata(self.token))
        except grpc.RpcError as e:
            raise ValueError(f"gRPC error: {e}")

    def log(self, message: str, step_run_id: str):
        try:
            request = PutLogRequest(
                stepRunId=step_run_id,
                createdAt=proto_timestamp_now(),
                message=message,
            )

            self.client.PutLog(request, metadata=get_metadata(self.token))
        except Exception as e:
            raise ValueError(f"Error logging: {e}")

    def stream(self, data: str | bytes, step_run_id: str):
        try:
            if isinstance(data, str):
                data_bytes = data.encode("utf-8")
            elif isinstance(data, bytes):
                data_bytes = data
            else:
                raise ValueError("Invalid data type. Expected str, bytes, or file.")

            request = PutStreamEventRequest(
                stepRunId=step_run_id,
                createdAt=proto_timestamp_now(),
                message=data_bytes,
            )
            self.client.PutStreamEvent(request, metadata=get_metadata(self.token))
        except Exception as e:
            raise ValueError(f"Error putting stream event: {e}")
