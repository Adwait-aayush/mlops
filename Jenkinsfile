pipeline {
    agent any

    environment {
        // Project name used for all image tags
        PROJECT     = "mlops"
        COMPOSE_PROJECT = ""
        SERVING_HOST_PORT = "18000"
        MONITORING_HOST_PORT = "18001"
        FRONTEND_HOST_PORT = "13000"
        SERVING_URL = "http://localhost:18000"
        MONITOR_URL = "http://localhost:18001"
        COMPOSE_CMD = ""
    }

    stages {

        // ── Stage 1: Checkout ──────────────────────────────────────
        stage('Checkout') {
            steps {
                echo '📥 Pulling latest code...'
                checkout scm
            }
        }

        // ── Stage 1.5: Resolve Compose Command ───────────────────
        stage('Resolve Compose') {
            steps {
                script {
                    def cmd = sh(
                        script: '''
                            if docker compose version >/dev/null 2>&1; then
                                echo "docker compose"
                            elif command -v docker-compose >/dev/null 2>&1; then
                                echo "docker-compose"
                            else
                                echo ""
                            fi
                        ''',
                        returnStdout: true
                    ).trim()

                    if (!cmd) {
                        error("Docker Compose is not available. Install docker compose plugin or docker-compose.")
                    }

                    env.COMPOSE_CMD = cmd
                    env.COMPOSE_PROJECT = "mlops-${env.BUILD_NUMBER}"
                    int offset = (env.BUILD_NUMBER as Integer) % 500
                    env.SERVING_HOST_PORT = "${18000 + offset}"
                    env.MONITORING_HOST_PORT = "${19000 + offset}"
                    env.FRONTEND_HOST_PORT = "${13000 + offset}"
                    env.SERVING_URL = "http://localhost:${env.SERVING_HOST_PORT}"
                    env.MONITOR_URL = "http://localhost:${env.MONITORING_HOST_PORT}"
                    echo "Using compose command: ${env.COMPOSE_CMD}"
                    echo "Using compose project: ${env.COMPOSE_PROJECT}"
                    echo "Using ports: serving=${env.SERVING_HOST_PORT}, monitoring=${env.MONITORING_HOST_PORT}, frontend=${env.FRONTEND_HOST_PORT}"
                }
            }
        }

        // ── Stage 2: Build All Images ──────────────────────────────
        stage('Build Images') {
            steps {
                echo '🔨 Building all Docker images...'
                sh "COMPOSE_PROJECT_NAME=${env.COMPOSE_PROJECT} ${env.COMPOSE_CMD} build"
            }
        }

        // ── Stage 3: Data Ingestion ────────────────────────────────
        // Downloads and validates the dataset
        // Pipeline stops here if data is bad
        stage('Data Ingestion') {
            steps {
                echo '📦 Running data ingestion...'
                sh "COMPOSE_PROJECT_NAME=${env.COMPOSE_PROJECT} ${env.COMPOSE_CMD} run --rm ingestion"
            }
        }

        // ── Stage 4: Train Model ───────────────────────────────────
        // Trains the spam classifier
        // Pipeline stops here if accuracy is below 80%
        stage('Train Model') {
            steps {
                echo '🤖 Training model...'
                sh "COMPOSE_PROJECT_NAME=${env.COMPOSE_PROJECT} ${env.COMPOSE_CMD} run --rm training"
            }
        }

        // ── Stage 5: Deploy Services ───────────────────────────────
        // Starts serving and monitoring containers
        stage('Deploy') {
            steps {
                echo '🚀 Deploying serving and monitoring...'
                sh "COMPOSE_PROJECT_NAME=${env.COMPOSE_PROJECT} SERVING_HOST_PORT=${env.SERVING_HOST_PORT} MONITORING_HOST_PORT=${env.MONITORING_HOST_PORT} FRONTEND_HOST_PORT=${env.FRONTEND_HOST_PORT} ${env.COMPOSE_CMD} up -d serving monitoring frontend"

                echo '⏳ Waiting for services to start...'
                sh 'sleep 20'
            }
        }

        // ── Stage 6: Health Check ──────────────────────────────────
        // Checks if serving API is up and responding
        stage('Health Check') {
            steps {
                echo '🏥 Checking service health...'
                sh '''
                    STATUS=$(curl -s ${SERVING_URL}/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get(\'status\', \'unknown\'))")
                    echo "Serving status: $STATUS"
                    if [ "$STATUS" != "ok" ]; then
                        echo "❌ Health check failed!"
                        exit 1
                    fi
                    echo "✅ Serving is healthy!"
                '''
            }
        }

        // ── Stage 7: Monitoring Gate ───────────────────────────────
        // Waits for monitoring to run checks then decides rollback or pass
        stage('Monitoring Gate') {
            steps {
                echo '📊 Waiting for monitoring checks...'
                sh 'sleep 30'

                echo '🔍 Checking monitoring status...'
                sh '''
                    HEALTHY=$(curl -s ${MONITOR_URL}/status | python3 -c "import sys,json; d=json.load(sys.stdin); print(str(d.get(\'healthy\', False)).lower())")
                    echo "Model healthy: $HEALTHY"
                    if [ "$HEALTHY" != "true" ]; then
                        echo "❌ Monitoring gate failed — model is unhealthy! Rolling back..."
                        COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT} ${COMPOSE_CMD} down
                        exit 1
                    fi
                    echo "✅ Monitoring gate passed — model is healthy!"
                '''
            }
        }

        // ── Stage 8: Full Rollout ──────────────────────────────────
        stage('Full Rollout') {
            steps {
                echo '🎉 All gates passed — deployment successful!'
                echo '✅ Services running:'
                sh "COMPOSE_PROJECT_NAME=${env.COMPOSE_PROJECT} ${env.COMPOSE_CMD} ps"
            }
        }
    }

    // ── Post Actions ───────────────────────────────────────────────
    post {
        success {
            echo '✅ Pipeline completed successfully! MLOps platform is live.'
        }
        failure {
            echo '❌ Pipeline failed. Check logs above.'
            sh "COMPOSE_PROJECT_NAME=${env.COMPOSE_PROJECT} ${env.COMPOSE_CMD} down || true"
        }
        always {
            echo '📋 Pipeline finished. Check http://localhost:3000 for dashboard.'
        }
    }
}