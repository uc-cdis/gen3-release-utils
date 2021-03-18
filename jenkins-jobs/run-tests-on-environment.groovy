/*
  String parameter TARGET_ENVIRONMENT
    e.g., qa-dcp

  String parameter TEST_SUITE
    e.g., test-portal-homepageTest
*/
node('gen3-qa-worker') {
  try {
    stage('Clean workspace') {
        cleanWs()
    }
    stage('Checkout source') {
        // cloud-automation
        checkout([
          $class: 'GitSCM',
          branches: [[name: 'refs/heads/master']],
          doGenerateSubmoduleConfigurations: false,
          extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: 'cloud-automation']],
          submoduleCfg: [],
          userRemoteConfigs: [[credentialsId: 'PlanXCyborgUser', url: 'https://github.com/uc-cdis/cloud-automation.git']]
        ])
        // gen3-qa
        checkout([
          $class: 'GitSCM',
          branches: [[name: 'refs/heads/master']],
          doGenerateSubmoduleConfigurations: false,
          extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: 'gen3-qa']],
          submoduleCfg: [],
          userRemoteConfigs: [[credentialsId: 'PlanXCyborgUser', url: 'https://github.com/uc-cdis/gen3-qa.git']]
        ])
    }
    stage('create test data (TODO)') {
        sh """
          mkdir testData
        """
    }
    stage('run tests') {
        withCredentials([file(credentialsId: 'fence-google-app-creds-secret', variable: 'GOOGLE_APP_CREDS_JSON')]) {
            def selectedTestLabel = TEST_SUITE.split("-")
            println "selected test: suites/" + selectedTestLabel[1] + "/" + selectedTestLabel[2] + ".js"
            def selectedTest = "suites/" + selectedTestLabel[1] + "/" + selectedTestLabel[2] + ".js"
            sh """
                cd gen3-qa
                export GEN3_HOME=../cloud-automation
                export TEST_DATA_PATH=../testData
                export GEN3_SKIP_PROJ_SETUP=true
                npm install

                NAMESPACE="${TARGET_ENVIRONMENT}" npm test -- --reporter mocha-multi $selectedTest
            """
        }
    }
  }catch (e) {
    throw e
  } finally {
    archiveArtifacts artifacts: 'gen3-qa/output/*'
  }
}
