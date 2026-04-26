pipeline {
    agent any

    stages {

        stage('Checkout') {
            steps {
                echo 'Pulling latest code...'
                checkout scm
            }
        }

        stage('Cleanup') {
            steps {
                echo 'Stopping any previously running containers...'
                bat 'docker compose down || true'
            }
        }

        stage('Build Images') {
            steps {
                echo 'Building all Docker images...'
                bat 'docker compose build'
            }
        }

        stage('Data Ingestion') {
            steps {
                echo 'Running data ingestion...'
                bat 'docker compose run --rm ingestion'
            }
        }

        stage('Train Model') {
            steps {
                echo 'Training model...'
                bat 'docker compose run --rm training'
            }
        }

        stage('Deploy') {
            steps {
                echo 'Deploying services...'
                bat 'docker compose up -d serving monitoring frontend'
                bat 'sleep 20'
            }
        }

        stage('Health Check') {
            steps {
                echo 'Checking serving health...'
                bat '''
                    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
                    echo "Health endpoint returned: $HTTP_CODE"
                    if [ "$HTTP_CODE" != "200" ]; then
                        echo "Health check failed!"
                        exit 1
                    fi
                    echo "Serving is healthy!"
                '''
            }
        }

        stage('Monitoring Gate') {
            steps {
                echo 'Waiting for monitoring checks...'
                bat 'sleep 30'
                bat '''
                    RESPONSE=$(curl -s http://localhost:8001/status)
                    echo "Monitoring response: $RESPONSE"
                    if echo "$RESPONSE" | grep -q 'healthy.*true'; then
                        echo "Monitoring gate passed!"
                    else
                        echo "Monitoring gate failed - rolling back!"
                        docker compose down
                        exit 1
                    fi
                '''
            }
        }
        
        stage('Kubernetes Deploy') { 
            steps {
                 echo 'Deploying to Kubernetes...'
                  bat 'kubectl apply -f k8s-manifests/batared-pvc.yaml'
                 bat 'kubectl apply -f k8s-manifests/ingestion.yaml' 
                 bat 'kubectl apply -f k8s-manifests/training.yaml' 
                 bat 'kubectl apply -f k8s-manifests/serving.yaml' 
                 bat 'kubectl apply -f k8s-manifests/monitoring.yaml' 
                 bat 'kubectl apply -f k8s-manifests/frontend.yaml' 
                 
                 echo 'Waiting for pods to be ready...' 
                 bat 'kubectl get pods' 
                 bat 'sleep 20'
                  }
         }
        stage('Kubernetes Check') {
             steps {
                 echo 'Checking Kubernetes deployment...'
                  bat 'kubectl get pods'
                   bat 'kubectl get services' 
                   }
     }

        stage('Full Rollout') {
            steps {
                echo 'All gates passed - deployment successful!'
                bat 'docker compose ps'
                bat 'kubectl get pods'
            }
        }
    }

    post {
        success {
            echo 'Pipeline completed! MLOps platform is live at http://localhost:3000'
        }
        failure {
            echo 'Pipeline failed. Rolling back...'
            bat 'docker compose down || true'
        }
        always {
            echo 'Done. Dabatboard at http://localhost:3000'
        }
    }
}