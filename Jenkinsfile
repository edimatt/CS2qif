pipeline {
    agent {
        docker {
            image 'younata/tox'
            args ''
            reuseNode true
        }
    }
    stages {
        stage('Integration') {
            steps {
                checkout scm
                sh 'tox'
            }
        }
    }
}

