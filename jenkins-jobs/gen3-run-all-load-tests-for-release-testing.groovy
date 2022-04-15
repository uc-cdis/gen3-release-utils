/*
  String parameter LIST_OF_LOAD_TEST_SCENARIOS
    Default value: fence-presigned-url,sheepdog-import-clinical-metada,metadata-service-create-and-query,metadata-service-filter-large-database

  String parameter RELEASE_VERSION
    e.g., 2021.04
*/

List<String> environments = Arrays.asList(LIST_OF_LOAD_TEST_SCENARIOS.split("\\s*,\\s*"));

def quietPeriod = 0;

def jenkins = Jenkins.getInstance()

def job = jenkins.getItem("gen3-run-load-tests");

environments.each {loadTestScenario ->
  println "Running load test for ${loadTestScenario}...";

  def params = []

  params += new StringParameterValue("LOAD_TEST_DESCRIPTOR", loadTestScenario);

  params += new StringParameterValue("TARGET_ENVIRONMENT", "qa-dcp");
  params += new StringParameterValue("PRESIGNED_URL_ACL_FILTER", "phs000178");
  params += new StringParameterValue("PRESIGNED_URL_AUTHZ_FILTER", "/programs/DEV/projects/test1,/programs/DEV/projects/test2,/programs/DEV/projects/test3");
  params += new StringParameterValue("SHEEPDOG_NUM_OF_RECORDS_TO_IMPORT", "100");
  params += new StringParameterValue("INDEXD_NUM_OF_RECORDS_TO_CREATE", "1000");
  params += new StringParameterValue("DESIRED_NUMBER_OF_FENCE_PODS", "10");
  params += new StringParameterValue("SIGNED_URL_PROTOCOL", "s3");
  params += new StringParameterValue("SQS_URL","https://sqs.us-east-1.amazonaws.com/707767160287/qaplanetv2--qa-niaid--audit-sqs");
  params += new StringParameterValue("MINIMUM_RECORDS", "10000");
  params += new StringParameterValue("RECORD_CHUNK_SIZE", "1024");
  params += new StringParameterValue("NUM_PARALLEL_REQUESTS", "5");
  params += new StringParameterValue("PASSPORTS_LIST", " ");
  params += new StringParameterValue("MTLS_DOMAIN", "ctds-test-env.planx-pla.net");

  params += new StringParameterValue("RELEASE_VERSION", "${RELEASE_VERSION}");

  def paramsAction = new ParametersAction(params);
  hudson.model.Hudson.instance.queue.schedule(job, quietPeriod, null, paramsAction);
  quietPeriod += 3600;
}
