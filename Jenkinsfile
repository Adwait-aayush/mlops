pipeline {
    agent any

    environment {
        COMPOSE_PROJECT_NAME = ''
        SERVING_HOST_PORT = ''
        MONITORING_HOST_PORT = ''
        FRONTEND_HOST_PORT = ''
        SERVING_URL = ''
        MONITOR_URL = ''
    }

    stages {

        stage('Checkout') {
            steps {
                echo '📥 Pulling latest code...'
                checkout scm
            }
        }

        stage('Resolve Runtime Config') {
            steps {
                script {
                    int offset = (env.BUILD_NUMBER as Integer) % 500
                    env.COMPOSE_PROJECT_NAME = "mlops-${env.BUILD_NUMBER}"
                    env.SERVING_HOST_PORT = "${18000 + offset}"
                    env.MONITORING_HOST_PORT = "${19000 + offset}"
                    env.FRONTEND_HOST_PORT = "${13000 + offset}"
                    env.SERVING_URL = "http://localhost:${env.SERVING_HOST_PORT}"
                    env.MONITOR_URL = "http://localhost:${env.MONITORING_HOST_PORT}"

                    echo "Using compose project: ${env.COMPOSE_PROJECT_NAME}"
                    echo "Using ports: serving=${env.SERVING_HOST_PORT}, monitoring=${env.MONITORING_HOST_PORT}, frontend=${env.FRONTEND_HOST_PORT}"
                }
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
                sh 'SERVING_HOST_PORT=${SERVING_HOST_PORT} MONITORING_HOST_PORT=${MONITORING_HOST_PORT} FRONTEND_HOST_PORT=${FRONTEND_HOST_PORT} docker compose up -d serving monitoring frontend'
                sh 'sleep 20'
            }
        }

        stage('Health Check') {
            steps {
                echo '🏥 Checking serving health...'
                sh '''
                    STATUS=$(curl -s ${SERVING_URL}/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','unknown'))")
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
                    HEALTHY=$(curl -s ${MONITOR_URL}/status | python3 -c "import sys,json; d=json.load(sys.stdin); print(str(d.get('healthy', False)).lower())")
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
            echo "✅ Pipeline completed! MLOps platform is live at http://localhost:${env.FRONTEND_HOST_PORT}"
        }
        failure {
            echo '❌ Pipeline failed. Rolling back...'
            sh 'docker compose down || true'
        }
        always {
            echo "📋 Done. Dashboard → http://localhost:${env.FRONTEND_HOST_PORT}"
        }
    }
}
