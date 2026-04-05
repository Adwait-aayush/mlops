pipeline {
    agent any

    environment {
        // Project name used for all image tags
        PROJECT     = "mlops"
        SERVING_URL = "http://localhost:8000"
        MONITOR_URL = "http://localhost:8001"
    }

    stages {

        // ── Stage 1: Checkout ──────────────────────────────────────
        stage('Checkout') {
            steps {
                echo '📥 Pulling latest code...'
                checkout scm
            }
        }

        // ── Stage 2: Build All Images ──────────────────────────────
        stage('Build Images') {
            steps {
                echo '🔨 Building all Docker images...'
                sh 'docker compose build'
            }
        }

        // ── Stage 3: Data Ingestion ────────────────────────────────
        // Downloads and validates the dataset
        // Pipeline stops here if data is bad
        stage('Data Ingestion') {
            steps {
                echo '📦 Running data ingestion...'
                sh 'docker compose run --rm ingestion'
            }
        }

        // ── Stage 4: Train Model ───────────────────────────────────
        // Trains the spam classifier
        // Pipeline stops here if accuracy is below 80%
        stage('Train Model') {
            steps {
                echo '🤖 Training model...'
                sh 'docker compose run --rm training'
            }
        }

        // ── Stage 5: Deploy Services ───────────────────────────────
        // Starts serving and monitoring containers
        stage('Deploy') {
            steps {
                echo '🚀 Deploying serving and monitoring...'
                sh 'docker compose up -d serving monitoring frontend'

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
                        docker compose down
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
                sh 'docker compose ps'
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
            sh 'docker compose down || true'
        }
        always {
            echo '📋 Pipeline finished. Check http://localhost:3000 for dashboard.'
        }
    }
}