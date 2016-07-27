"""
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

"""

import sys, os, pwd
from resource_management import *
from resource_management.libraries.functions import check_process_status
from subprocess import call

class Master(Script):
  def install(self, env):
    self.install_packages(env)
    import params
    import status_params

    Execute('echo Scriptdir is: ' + params.service_scriptsdir)

    Execute('echo installation directory is: ' + params.tweet_installdir)
    Execute('echo ambari host: ' + params.ambari_server_host)
    Execute('echo namenode host: ' + params.namenode_host)
    Execute('echo nimbus host: ' + params.nimbus_host)
    Execute('echo hive host: ' + params.hive_metastore_host)
    Execute('echo hbase host: ' + params.hbase_master_host)
    Execute('echo kafka broker: ' + params.kafka_broker_host)


    Directory(params.tweet_installdir, mode=0755, owner='root', group='root', recursive=True)
    Directory(status_params.tweet_piddir, mode=0755, owner='root', group='root', recursive=True)

    Execute('echo Copying script to ' + params.tweet_installdir)
    Execute('cp -f ' + params.service_scriptsdir + 'twitter_dashboard_v5.xml ' + params.tweet_installdir)
    Execute('cp -f ' + params.service_scriptsdir + 'banana_default.json ' + params.tweet_installdir)
    Execute('cp -f ' + params.service_scriptsdir + 'kiwi_default.json ' + params.tweet_installdir)
    Execute('cp -f ' + params.service_scriptsdir + 'twitterAll_configsets.tgz ' + params.tweet_installdir)
    Execute('cp -f ' + params.service_scriptsdir + 'twittersMap_configsets.tgz ' + params.tweet_installdir)

    Execute('tar -xf ' + params.tweet_installdir + '/twitterAll_configsets.tgz -C /opt/lucidworks-hdpsearch/solr/server/solr/configsets/')
    Execute('tar -xf ' + params.tweet_installdir + '/twittersMap_configsets.tgz -C /opt/lucidworks-hdpsearch/solr/server/solr/configsets/')

    Execute('su - hdfs -c "hdfs dfs -mkdir -p /solr"')
    Execute('su - hdfs -c "hdfs dfs -chown solr /solr"')
    Execute('su - hdfs -c "hdfs dfs -mkdir -p /demotweets"')
    Execute('su - hdfs -c "hdfs dfs -chown root /demotweets"')

    Execute('/opt/lucidworks-hdpsearch/solr/bin/solr create -c twitterAll -d /opt/lucidworks-hdpsearch/solr/server/solr/configsets/data_driven_schema_configs_twitterAll/conf -n twitterAll -s 1 -rf 1')
    Execute('/opt/lucidworks-hdpsearch/solr/bin/solr create -c twittersMap -d /opt/lucidworks-hdpsearch/solr/server/solr/configsets/data_driven_schema_configs_twittersMap/conf -n twittersMap -s 1 -rf 1')

    Execute('cp -pR /opt/lucidworks-hdpsearch/solr/server/solr-webapp/webapp/banana /opt/lucidworks-hdpsearch/solr/server/solr-webapp/webapp/kiwi')
    Execute('cp ' + params.tweet_installdir + '/banana_default.json  /opt/lucidworks-hdpsearch/solr/server/solr-webapp/webapp/banana/app/dashboards/default.json')
    Execute('cp ' + params.tweet_installdir + '/kiwi_default.json /opt/lucidworks-hdpsearch/solr/server/solr-webapp/webapp/kiwi/app/dashboards/default.json')

    Execute('echo Add repo for maven')
    Execute('curl -o /etc/yum.repos.d/epel-apache-maven.repo https://repos.fedorapeople.org/repos/dchen/apache-maven/epel-apache-maven.repo')
    Execute('echo Install maven')
    Execute('yum -y install apache-maven')
    Execute('echo Clone ifram-view repo')
    Execute('git clone https://github.com/abajwa-hw/iframe-view.git /opt/iframe-view')
    Execute('echo Execute sed')
    Execute('sed -i "s/iFrame View/Banana dashboard/g" /opt/iframe-view/src/main/resources/view.xml')
    Execute('sed -i "s/IFRAME_VIEW/BANANA_DASHBOARD/g" /opt/iframe-view/src/main/resources/view.xml')
    Execute('sed -i "s/6080/8983\/solr\/banana\/index.html/g" /opt/iframe-view/src/main/resources/index.html')
    Execute('sed -i "s/iframe-view/banana_dashboard-view/g" /opt/iframe-view/pom.xml')
    Execute('sed -i "s/Ambari iFrame View/Banana dashboard view/g" /opt/iframe-view/pom.xml')
    Execute('echo Compile mvn')
    Execute('mvn -f /opt/iframe-view/pom.xml clean package')
    Execute('echo Copy JAR')
    Execute('cp /opt/iframe-view/target/*jar /var/lib/ambari-server/resources/views/banana_view.jar')


    Execute('sed -i "s/iFrame View/Kiwi dashboard/g" /opt/iframe-view/src/main/resources/view.xml')
    Execute('sed -i "s/IFRAME_VIEW/KIWI_DASHBOARD/g" /opt/iframe-view/src/main/resources/view.xml')
    Execute('sed -i "s/6080/8983\/solr\/kiwi\/index.html/g" /opt/iframe-view/src/main/resources/index.html')
    Execute('sed -i "s/iframe-view/kiwi_dashboard-view/g" /opt/iframe-view/pom.xml')
    Execute('sed -i "s/Ambari iFrame View/Kiwi dashboard view/g" /opt/iframe-view/pom.xml')
    Execute('rm -rf /opt/iframe-view/target')
    Execute('echo Compile mvn')
    Execute('mvn -f /opt/iframe-view/pom.xml clean package')
    Execute('echo Copy JAR')
    Execute('cp /opt/iframe-view/target/*jar /var/lib/ambari-server/resources/views/kiwi_view.jar')
    self.configure(env)
   
  def configure(self, env):
    import params
    import status_params
    env.set_params(params)
    env.set_params(status_params)
    user_env=InlineTemplate(status_params.user_env)
    File(params.tweet_installdir + '/user-env.sh', content=user_env, owner='root',group='root')
    tweet_env=InlineTemplate(params.tweet_env)
    File(params.tweet_installdir + '/tweet-env.sh', content=tweet_env, owner='root',group='root')


  def stop(self, env):
    import params
    import status_params
    import requests
    self.configure(env)
    f = open(status_params.tweet_pidfile,"r")
    p_group_id = f.read()
    f.close()
    host = params.nifi_master_host + ':' + str(params.nifi_port)
    version = requests.get('http://' + host + '/nifi-api/controller/revision').json()["revision"]["version"]
    req = 'http://' + host + '/nifi-api/controller/process-groups/root/process-group-references/' + p_group_id.strip()                
    r = requests.put(req, data={'running':'false', 'version':version, 'clientId':'demotweet'})
    Execute('rm ' + status_params.tweet_pidfile, ignore_failures=True)

  def start(self, env):
    import params
    import status_params
    self.configure(env)
    #config_nifi_script = os.path.join(params.tweet_installdir,'setup_nifi.sh')
    nifi_template_xml = os.path.join(params.tweet_installdir,'twitter_dashboard_v5.xml')
    Execute ('pip install requests')
    if not os.path.exists(status_params.tweet_piddir):
        os.makedirs(status_params.tweet_piddir)
    #To change. Really bad!!!
    Execute ('echo Wait 30 seconds to let NiFi starts')
    Execute ('sleep 30')
    import requests
    # Setup NiFi
    nifi_controller_api = 'http://' + params.nifi_master_host + ':' + str(params.nifi_port) + '/nifi-api/controller/'
    p_group = requests.get(nifi_controller_api+'search-results?q=twitter_dashboard').json()["searchResultsDTO"]["processGroupResults"]
    if len(p_group) != 0 :
      Execute('echo ' +  "Process group " + p_group[0]["id"] + " already exists.")
    else:
      import xml.etree.ElementTree
      template_name=xml.etree.ElementTree.parse(nifi_template_xml).find(".//name").text
      template_id=""
      for template in requests.get(nifi_controller_api+'templates').json()["templates"] :
        if template["name"] == template_name:
          template_id = template["id"]
          break
      
      if template_id == "":
        tmplXML = requests.post(nifi_controller_api+'templates', files={'template':open(nifi_template_xml,'rb')})
        template_id = xml.etree.ElementTree.fromstring(tmplXML.text).find(".//id").text
      
      revision = requests.get(nifi_controller_api + 'revision').json()["revision"]["version"]
      Execute('echo ' +  str(revision) )
      r = requests.post(nifi_controller_api + 'process-groups/root/template-instance', data={'version':revision, 'clientId':'demotweet', 'templateId':template_id, 'originX':0, 'originY':0, 'process-group-id':'root'})
      p_group_id = r.json()["contents"]["processGroups"][0]["id"]
      Execute('echo "Created process group '+ str(p_group_id) + '"')
    #Execute ('chmod +x ' + config_nifi_script)
    #Execute (config_nifi_script + ' ' + params.tweet_installdir + ' ' + nifi_template_xml + ' ')
    #config_twitter_script = os.path.join(params.tweet_installdir,'setup_twitter.sh')
    #Setup twitter
    tweet_processor  = requests.get(nifi_controller_api+'search-results?q=GetTwitter').json()["searchResultsDTO"]["processorResults"][0]
    revision = requests.get(nifi_controller_api + 'revision').json()["revision"]["version"]
    Execute('echo "Tweet processor id: ' + str(tweet_processor["id"]) + '"')
    Execute('echo "Tweet group id: ' + str(tweet_processor["groupId"]) + '"')
    JSON="""{"revision": 
{"clientId": "demotweet","version":""" + str(revision) + """}, 
"processor": 
{"id": \"""" + str(tweet_processor["id"]) + """", 
"config": 
{"properties": 
{"Consumer Key": \"""" +str(params.consumer_key)+"""",
"Consumer Secret": \""""+str(params.consumer_secret)+"""",
"Access Token": \""""+str(params.access_token)+"""",
"Access Token Secret": \""""+str(params.access_secret)+"""",
"Terms to Filter On": \""""+str(params.filter_terms)+""""
}}}}"""
    requests.put(nifi_controller_api + "process-groups/"+tweet_processor["groupId"]+"/processors/"+tweet_processor["id"],data=JSON, headers = {'Content-type': 'application/json' })
    revision = requests.get(nifi_controller_api + 'revision').json()["revision"]["version"]
    requests.put(nifi_controller_api + 'process-groups/root/process-group-references/' + tweet_processor["groupId"], data={'running':'true', 'version':revision, 'clientId':'demotweet'})
    f=open(status_params.tweet_pidfile, 'w')
    f.write(tweet_processor["groupId"])
    f.close()
    #Execute ('chmod +x ' + config_twitter_script)
    #Execute (config_twitter_script + ' ' + params.tweet_installdir + ' GetTwitter ')

  def status(self, env):
    import status_params
    self.check_flow_running(status_params.tweet_pidfile, "sandbox.hortonworks.com", "9090")



  def check_flow_running(self, pid_file, host, port):
    import requests
    if not pid_file or not os.path.isfile(pid_file):
      raise ComponentIsNotRunning()
    try:
      f = open(pid_file,"r")
      p_group_id = f.read()
      f.close()
      req = 'http://' + host + ':' + port + '/nifi-api/controller/process-groups/root/process-group-references/' + p_group_id.strip()
      r = requests.get(req)
      if r.status_code != requests.codes.ok:
        raise ComponentIsNotRunning()
      if r.json()["processGroup"]["runningCount"] < 26:
        raise ComponentIsNotRunning()
    except Exception, e:
      raise ComponentIsNotRunning()
    
if __name__ == "__main__":
  Master().execute() 
