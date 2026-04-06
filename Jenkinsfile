pipeline {
    agent any

    stages {

        stage('Checkout') {
            steps {
                echo '📥 Pulling latest code...'
                checkout scm
            }
        }

        stage('Build Images') {
            steps {
                echo '🔨 Building all Docker images...'
                sh 'docker compose build'
            }
        }

        stage('Data Ingestion') {
            steps {
                echo '📦 Running data ingestion...'
                sh 'docker compose run --rm ingestion'
            }
        }

        stage('Train Model') {
            steps {
                echo '🤖 Training model...'
                sh 'docker compose run --rm training'
            }
        }

        stage('Deploy') {
            steps {
                echo '🚀 Deploying services...'
                sh 'docker compose up -d serving monitoring frontend'
                sh 'sleep 20'
            }
        }

        stage('Health Check') {
            steps {
                echo '🏥 Checking serving health...'
                sh '''
                    STATUS=$(curl -s http://localhost:8000/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','unknown'))")
                    echo "Serving status: $STATUS"
                    if [ "$STATUS" != "ok" ]; then
                        echo "Health check failed!"
                        exit 1
                    fi
                    echo "Serving is healthy!"
                '''
            }
        }

        stage('Monitoring Gate') {
            steps {
                echo '📊 Waiting for monitoring checks...'
                sh 'sleep 30'
                sh '''
                    HEALTHY=$(curl -s http://localhost:8001/status | python3 -c "import sys,json; d=json.load(sys.stdin); print(str(d.get('healthy', False)).lower())")
                    echo "Model healthy: $HEALTHY"
                    if [ "$HEALTHY" != "true" ]; then
                        echo "Monitoring gate failed — rolling back!"
                        docker compose down
                        exit 1
                    fi
                    echo "Monitoring gate passed!"
                '''
            }
        }

        stage('Full Rollout') {
            steps {
                echo '🎉 All gates passed — deployment successful!'
                sh 'docker compose ps'
            }
        }
    }

    post {
        success {
            echo '✅ Pipeline completed! MLOps platform is live at http://localhost:3000'
        }
        failure {
            echo '❌ Pipeline failed. Rolling back...'
            sh 'docker compose down || true'
        }
        always {
            echo '📋 Done. Dashboard → http://localhost:3000'
        }
    }
}
