"""
RabbitMQ Connection Module
RabbitMQ 연결 및 메시지 발행
"""

import os
import ssl
import pika
import json
import logging
from typing import Any, Iterable

logger = logging.getLogger(__name__)


def _build_ssl_options(params: pika.URLParameters) -> pika.SSLOptions | None:
    """
    RabbitMQ URL이 TLS를 사용할 때 SSL 옵션을 생성합니다.

    :param params: RabbitMQ connection params.
    :return: SSL options 또는 None.
    """
    uses_tls = params.ssl_options is not None or params.port == 5671
    if not uses_tls:
        return None

    ssl_context = ssl.create_default_context()
    cafile = os.getenv("RABBITMQ_CA_CERT")
    if cafile:
        ssl_context.load_verify_locations(cafile=cafile)

    if os.getenv("RABBITMQ_SKIP_TLS_VERIFY", "").lower() == "true":
        logger.warning("RabbitMQ TLS verification is disabled by configuration")
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

    server_hostname = params.host if ssl_context.check_hostname else None
    return pika.SSLOptions(ssl_context, server_hostname=server_hostname)

def get_rabbitmq_connection():
    """
    RabbitMQ 연결 생성

    Returns:
        pika.BlockingConnection: RabbitMQ 연결 객체
    """
    rabbitmq_url = os.getenv("RABBITMQ_HOST")

    if not rabbitmq_url:
        raise ValueError("RABBITMQ_HOST environment variable not set")

    try:
        # URL 파싱하여 연결 파라미터 생성
        params = pika.URLParameters(rabbitmq_url)
        ssl_options = _build_ssl_options(params)
        if ssl_options is not None:
            params.ssl_options = ssl_options

        connection = pika.BlockingConnection(params)
        return connection
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}")
        raise

def _publish_messages(channel: pika.adapters.blocking_connection.BlockingChannel, queue_name: str, messages: Iterable[dict[str, Any]]) -> None:
    """
    동일 채널로 여러 메시지를 발행합니다.

    :param channel: RabbitMQ 채널.
    :param queue_name: 큐 이름.
    :param messages: 발행할 메시지 목록.
    :return: None.
    """
    channel.queue_declare(queue=queue_name, durable=False)
    for message in messages:
        channel.basic_publish(
            exchange="",
            routing_key=queue_name,
            body=json.dumps(message, ensure_ascii=False),
            properties=pika.BasicProperties(delivery_mode=2),
        )


def publish_message(queue_name: str, message: dict[str, Any]) -> None:
    """
    RabbitMQ 큐에 메시지 발행

    Args:
        queue_name: 큐 이름
        message: 발행할 메시지 (dict)
    """
    connection = None
    try:
        # 연결 생성
        connection = get_rabbitmq_connection()
        channel = connection.channel()

        _publish_messages(channel, queue_name, [message])

    except Exception as e:
        logger.error(f"Failed to publish message to RabbitMQ: {e}")
        raise
    finally:
        if connection and not connection.is_closed:
            connection.close()


def publish_messages(queue_name: str, messages: list[dict[str, Any]]) -> None:
    """
    하나의 연결로 여러 RabbitMQ 메시지를 발행합니다.

    :param queue_name: 큐 이름.
    :param messages: 발행할 메시지 목록.
    :return: None.
    """
    if not messages:
        return

    connection = None
    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        _publish_messages(channel, queue_name, messages)
    except Exception as e:
        logger.error(f"Failed to publish messages to RabbitMQ: {e}")
        raise
    finally:
        if connection and not connection.is_closed:
            connection.close()
