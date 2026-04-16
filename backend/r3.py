#!/usr/bin/env python3
import pika
import json
import os

conn = pika.BlockingConnection(
    pika.ConnectionParameters(
        host=os.getenv('RABBITMQ_HOST', 'rabbitmq'),
        credentials=pika.PlainCredentials('guest', 'guest')
    )
)
ch = conn.channel()

ids = [
    '947ad078-d43f-4290-b7bf-92d0598446c5',
    '518d8196-f7be-4d1b-9fe7-bede2f2b2ffe',
    '0c543ef3-6132-4c16-b3d0-e1d8b6b920b2',
    '7b2ff609-d07f-47db-a966-c9a324e345aa',
    'f95043c9-f9e3-4195-b1c9-bbbb20904385',
]

for rid in ids:
    ch.basic_publish(exchange='', routing_key='resume_queue',
        body=json.dumps({'resume_id': rid, 'file_path': f'/tmp/resumes/{rid}.pdf', 'job_description': 'Python developer'}),
        properties=pika.BasicProperties(delivery_mode=2))

print(f"✅ Republished {len(ids)} resumes")
conn.close()
