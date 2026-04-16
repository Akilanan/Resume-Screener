#!/usr/bin/env python3
"""Manually republish stuck resumes to the queue - run inside Docker container"""
import pika
import json
import sys
import os

def republish_stuck_resumes():
    """Republish the stuck resumes to the queue"""
    
    # RabbitMQ connection via Docker network
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=os.getenv('RABBITMQ_HOST', 'rabbitmq'),
                port=5672,
                credentials=pika.PlainCredentials('guest', 'guest'),
                connection_attempts=3,
                retry_delay=2
            )
        )
        channel = connection.channel()
        print("✅ Connected to RabbitMQ successfully")
    except Exception as e:
        print(f"❌ Failed to connect to RabbitMQ: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Test data for the stuck resumes
    stuck_resumes = [
        {
            'resume_id': '4436669c-e741-46ab-85d2-b58b1beffe59',
            'filename': 'sofia_rodriguez_resume.pdf'
        },
        {
            'resume_id': 'f410eca3-55d8-4227-a301-6266c677311f',
            'filename': 'david_chen_resume.pdf'
        },
        {
            'resume_id': 'a089c697-4fab-4dbc-a45f-1a256626a68d',
            'filename': 'aisha_patel_resume.pdf'
        },
        {
            'resume_id': '8922ecb0-372b-409d-a82b-abe2f3e819b5',
            'filename': 'marcus_johnson_resume.pdf'
        },
        {
            'resume_id': 'd10e85ec-ca9a-4467-b42b-3b7051566229',
            'filename': 'priya_sharma_resume.pdf'
        },
    ]
    
    try:
        # Just publish to existing queue without declaring it
        count = 0
        for resume in stuck_resumes:
            message = {
                'resume_id': resume['resume_id'],
                'file_path': f"/tmp/resumes/{resume['resume_id']}.pdf",
                'job_description': 'Looking for Python developer with ML experience and 5+ years experience'
            }
            
            channel.basic_publish(
                exchange='',
                routing_key='resume_queue',
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2  # Make message persistent
                )
            )
            print(f"✅ Republished: {resume['filename']}")
            count += 1
        
        print(f"\n✅ Total republished: {count} resumes to resume_queue")
        connection.close()
        print("✅ Connection closed")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    republish_stuck_resumes()
