pipeline {
    agent {
        docker {
            image 'edimatt/tox:1.0'
            args ''
            reuseNode true
        }
    }
    stages {
        stage('Integration') {
            steps {
                sh 'tox -e py36'
            }
        }
    }
    post {
        always {
            junit 'test-results.xml'
            cobertura coberturaReportFile: 'coverage.xml'
        }
    } 
}

