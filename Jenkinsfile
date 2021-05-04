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
            junit 'build/test-results.xml'
            cobertura coberturaReportFile: 'build/coverage.xml'
            publishHTML (target: [
                allowMissing: false,
                alwaysLinkToLastBuild: false,
                keepAll: true,
                reportDir: 'build/htmlcov',
                reportFiles: 'index.html',
                reportName: 'Code coverage'
            ])
        }
    } 
}

