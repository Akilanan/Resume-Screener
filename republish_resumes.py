#!/usr/bin/env python3
"""Manually republish stuck resumes to the queue"""
import os
import sys
import pika
import json
import uuid

# Set environment for local testing
os.environ['RABBITMQ_HOST'] = 'localhost'

# RabbitMQ connection
def get_rabbitmq_connection():
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host='localhost',
                port=5672,
                credentials=pika.PlainCredentials('guest', 'guest')
            )
        )
        return connection
    except Exception as e:
        print(f"❌ Failed to connect to RabbitMQ: {e}")
        print("Make sure RabbitMQ container is accessible from host at localhost:5672")
        sys.exit(1)

def republish_stuck_resumes():
    """Republish the stuck resumes to the queue"""
    
    # Test data for the stuck resumes
    stuck_resumes = [
        {
            'resume_id': '4436669c-e741-46ab-85d2-b58b1beffe59',
            'filename': 'sofia_rodriguez_resume.pdf',
            'file_path': '/tmp/resumes/4436669c-e741-46ab-85d2-b58b1beffe59.pdf'
        },
        {
            'resume_id': 'f410eca3-55d8-4227-a301-6266c677311f',
            'filename': 'david_chen_resume.pdf',
            'file_path': '/tmp/resumes/f410eca3-55d8-4227-a301-6266c677311f.pdf'
        },
        {
            'resume_id': 'a089c697-4fab-4dbc-a45f-1a256626a68d',
            'filename': 'aisha_patel_resume.pdf',
            'file_path': '/tmp/resumes/a089c697-4fab-4dbc-a45f-1a256626a68d.pdf'
        },
        {
            'resume_id': '8922ecb0-372b-409d-a82b-abe2f3e819b5',
            'filename': 'marcus_johnson_resume.pdf',
            'file_path': '/tmp/resumes/8922ecb0-372b-409d-a82b-abe2f3e819b5.pdf'
        },
        {
            'resume_id': 'd10e85ec-ca9a-4467-b42b-3b7051566229',
            'filename': 'priya_sharma_resume.pdf',
            'file_path': '/tmp/resumes/d10e85ec-ca9a-4467-b42b-3b7051566229.pdf'
        },
    ]
    
    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        
        # Declare the queue (same as backend does)
        channel.queue_declare(
            queue='resume_queue',
            durable=True,
            arguments={
                'x-dead-letter-exchange': 'resume_dlx',
                'x-dead-letter-routing-key': 'resume_dlq'
            }
        )
        
        print("✅ Connected to RabbitMQ successfully\n")
        
        # Republish each stuck resume
        for resume in stuck_resumes:
            message = {
                'resume_id': resume['resume_id'],
                'file_path': resume['file_path'],
                'job_description': 'Looking for Python developer'  # Generic job description
            }
            
            channel.basic_publish(
                exchange='',
                routing_key='resume_queue',
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2  # Make message persistent
                )
            )
            print(f"✅ Republished: {resume['filename']} (ID: {resume['resume_id'][:8]}...)")
        
        print(f"\n✅ Total republished: {len(stuck_resumes)} resumes")
        
        connection.close()
        print("✅ Queue connection closed\n")
        
        # Verify messages in queue
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        method, properties, body = channel.basic_get('resume_queue', auto_ack=False)
        if method:
            print(f"✅ Queue has messages! First message: {body[:100]}...")
            channel.basic_nack(method.delivery_tag)
        connection.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    republish_stuck_resumes()
