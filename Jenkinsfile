def composeCmd = ''
def composeProjectName = ''
def servingHostPort = '18000'
def monitoringHostPort = '18001'
def frontendHostPort = '13000'
def servingUrl = 'http://localhost:18000'
def monitorUrl = 'http://localhost:18001'

pipeline {
    agent any

    environment {
        // Project name used for all image tags
        PROJECT     = "mlops"
        
        SERVING_HOST_PORT = "18000"
        MONITORING_HOST_PORT = "18001"
        FRONTEND_HOST_PORT = "13000"
        SERVING_URL = "http://localhost:18000"
        MONITOR_URL = "http://localhost:18001"
       
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

                    composeCmd = cmd
                    composeProjectName = "mlops-${env.BUILD_NUMBER}"
                    int offset = (env.BUILD_NUMBER as Integer) % 500
                    servingHostPort = "${18000 + offset}"
                    monitoringHostPort = "${19000 + offset}"
                    frontendHostPort = "${13000 + offset}"
                    servingUrl = "http://localhost:${servingHostPort}"
                    monitorUrl = "http://localhost:${monitoringHostPort}"

                    env.COMPOSE_CMD = composeCmd
                    env.COMPOSE_PROJECT_NAME = composeProjectName
                    env.SERVING_HOST_PORT = servingHostPort
                    env.MONITORING_HOST_PORT = monitoringHostPort
                    env.FRONTEND_HOST_PORT = frontendHostPort
                    env.SERVING_URL = servingUrl
                    env.MONITOR_URL = monitorUrl

                    echo "Using compose command: ${composeCmd}"
                    echo "Using compose project: ${composeProjectName}"
                    echo "Using ports: serving=${servingHostPort}, monitoring=${monitoringHostPort}, frontend=${frontendHostPort}"
                }
            }
        }

        // ── Stage 2: Build All Images ──────────────────────────────
        stage('Build Images') {
            steps {
                echo '🔨 Building all Docker images...'
                sh "COMPOSE_PROJECT_NAME=${composeProjectName} ${composeCmd} build"
            }
        }

        // ── Stage 3: Data Ingestion ────────────────────────────────
        // Downloads and validates the dataset
        // Pipeline stops here if data is bad
        stage('Data Ingestion') {
            steps {
                echo '📦 Running data ingestion...'
                sh "COMPOSE_PROJECT_NAME=${composeProjectName} ${composeCmd} run --rm ingestion"
            }
        }

        // ── Stage 4: Train Model ───────────────────────────────────
        // Trains the spam classifier
        // Pipeline stops here if accuracy is below 80%
        stage('Train Model') {
            steps {
                echo '🤖 Training model...'
                sh "COMPOSE_PROJECT_NAME=${composeProjectName} ${composeCmd} run --rm training"
            }
        }

        // ── Stage 5: Deploy Services ───────────────────────────────
        // Starts serving and monitoring containers
        stage('Deploy') {
            steps {
                echo '🚀 Deploying serving and monitoring...'
                sh "COMPOSE_PROJECT_NAME=${composeProjectName} SERVING_HOST_PORT=${servingHostPort} MONITORING_HOST_PORT=${monitoringHostPort} FRONTEND_HOST_PORT=${frontendHostPort} ${composeCmd} up -d serving monitoring frontend"

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
                sh "COMPOSE_PROJECT_NAME=${composeProjectName} ${composeCmd} ps"
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
            sh "COMPOSE_PROJECT_NAME=${composeProjectName} ${composeCmd} down || true"
        }
        always {
            echo '📋 Pipeline finished. Check http://localhost:3000 for dashboard.'
        }
    }
}