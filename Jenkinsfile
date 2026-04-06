pipeline {
    agent any

    stages {

        stage('Checkout') {
            steps {
                echo '📥 Pulling latest code...'
                checkout scm
            }
        }

        stage('Cleanup') {
            steps {
                echo '🧹 Stopping any previously running containers...'
                sh 'docker compose down || true'
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
                    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
                    echo "Health endpoint returned: $HTTP_CODE"
                    if [ "$HTTP_CODE" != "200" ]; then
                        echo "Health check failed — got $HTTP_CODE instead of 200!"
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
                    RESPONSE=$(curl -s http://localhost:8001/status)
                    echo "Monitoring response: $RESPONSE"
                    if echo "$RESPONSE" | grep -q '"healthy": true'; then
                        echo "Monitoring gate passed!"
                    else
                        echo "Monitoring gate failed — rolling back!"
                        docker compose down
                        exit 1
                    fi
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