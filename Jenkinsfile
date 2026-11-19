pipeline {
  agent { 
    label 'k8s-master'   
  }

  options {
    timestamps()
    disableConcurrentBuilds()
    buildDiscarder(logRotator(numToKeepStr: '15'))
  }

  environment {
    DOCKERUSER = "ambuj2k19"
    TAG        = "${env.BUILD_NUMBER}"
    DEV_HOST   = "app-dev.local.lab"
    PROD_HOST  = "app.local.lab"
  }

  stages {

    stage('Checkout') {
      steps { checkout scm }
    }

    stage('Unit Test') {
      steps {
        sh '''
          cd backend
          python3 -m venv .venv
          . .venv/bin/activate
          pip install -q -r requirements.txt
          pytest -q
        '''
      }
    }

    stage('Build Images') {
      steps {
        sh '''
          docker build -t $DOCKERUSER/myapp-backend:$TAG  ./backend
          docker build -t $DOCKERUSER/myapp-frontend:$TAG ./frontend
        '''
      }
    }

    stage('Push to Docker Hub') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'dockerhub-creds',
                                          usernameVariable: 'DH_USER',
                                          passwordVariable: 'DH_PASS')]) {
          sh '''
            echo "$DH_PASS" | docker login -u "$DH_USER" --password-stdin
            docker push $DOCKERUSER/myapp-backend:$TAG
            docker push $DOCKERUSER/myapp-frontend:$TAG
            docker logout
          '''
        }
      }
    }

    stage('Deploy to DEV') {
      steps { script { deployTo('dev', env.DEV_HOST) } }
    }

    stage('Approve PROD') {
      steps {
        timeout(time: 30, unit: 'MINUTES') {
          input message: "Deploy build #${env.BUILD_NUMBER} to PRODUCTION?", ok: 'Deploy'
        }
      }
    }

    stage('Deploy to PROD') {
      steps { script { deployTo('prod', env.PROD_HOST) } }
    }
  }

  post {
    always  { sh 'docker image prune -f || true' }
    success { echo "Build #${env.BUILD_NUMBER} deployed successfully." }
    failure { echo "Build #${env.BUILD_NUMBER} FAILED." }
  }
}

def deployTo(String ns, String host) {
  withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
    sh """
      rm -rf rendered && mkdir rendered && cp k8s/*.yaml rendered/
      sed -i 's|__DOCKERUSER__|${DOCKERUSER}|g; s|__TAG__|${TAG}|g; s|__HOST__|${host}|g' rendered/*.yaml

      kubectl apply -n ${ns} -f rendered/
      kubectl rollout status statefulset/postgres -n ${ns} --timeout=180s
    """
    try {
      sh """
        kubectl rollout status deployment/backend  -n ${ns} --timeout=120s
        kubectl rollout status deployment/frontend -n ${ns} --timeout=120s
      """
    } catch (err) {
      sh """
        echo 'Rollout failed, rolling back in ${ns}'
        kubectl rollout undo deployment/backend  -n ${ns} || true
        kubectl rollout undo deployment/frontend -n ${ns} || true
      """
      error("Deployment to ${ns} failed and was rolled back")
    }
  }
}
