import sys

from discovery.service.service import AbstractPropertyBuilder
from discovery.utils.constants import DEFAULT_KEY
from discovery.utils.inventory import CPInventoryManager
from discovery.utils.services import ConfluentServices, ServiceData
from discovery.utils.utils import InputContext, Logger, FileUtils, get_listener_details

logger = Logger.get_logger()

class_name = ""


class KsqlServicePropertyBuilder:

    @staticmethod
    def build_properties(input_context: InputContext, inventory: CPInventoryManager):
        from discovery.service import get_service_builder_class
        builder_class = get_service_builder_class(modules=sys.modules[__name__],
                                                  default_class_name="KsqlServicePropertyBaseBuilder",
                                                  version=input_context.from_version)
        global class_name
        class_name = builder_class
        builder_class(input_context, inventory).build_properties()


class KsqlServicePropertyBaseBuilder(AbstractPropertyBuilder):
    inventory = None
    input_context = None
    hosts = []

    def __init__(self, input_context: InputContext, inventory: CPInventoryManager):
        self.inventory = inventory
        self.input_context = input_context
        self.mapped_service_properties = set()
        self.service = ConfluentServices(input_context).KSQL()
        self.group = self.service.group

    def build_properties(self):

        # Get the hosts for given service
        hosts = self.get_service_host(self.service, self.inventory)
        self.hosts = hosts

        if not hosts:
            logger.error(f"Could not find any host with service {self.service.name} ")
            return

        host_service_properties = self.get_property_mappings(self.input_context, self.service, hosts)
        service_properties = host_service_properties.get(hosts[0]).get(DEFAULT_KEY)

        # Build service user group properties
        self.__build_daemon_properties(self.input_context, self.service, hosts)

        # Build service properties
        self.__build_service_properties(service_properties)

        # Add custom properties
        self.__build_custom_properties(host_service_properties, self.mapped_service_properties)

        # Build Command line properties
        self.__build_runtime_properties(hosts)

    def __build_daemon_properties(self, input_context: InputContext, service: ServiceData, hosts: list):

        # User group information
        response = self.get_service_user_group(input_context, service, hosts)
        self.update_inventory(self.inventory, response)

    def __build_service_properties(self, service_properties):
        for key, value in vars(class_name).items():
            if callable(getattr(class_name, key)) and key.startswith("_build"):
                func = getattr(class_name, key)
                logger.info(f"Calling Ksql property builder.. {func.__name__}")
                result = func(self, service_properties)
                self.update_inventory(self.inventory, result)

    def __build_custom_properties(self, host_service_properties: dict, mapped_properties: set):

        custom_group = "ksql_custom_properties"
        skip_properties = set(FileUtils.get_ksql_configs("skip_properties"))

        _host_service_properties = dict()
        for host in host_service_properties.keys():
            _host_service_properties[host] = host_service_properties.get(host).get(DEFAULT_KEY)
        self.build_custom_properties(inventory=self.inventory, group=self.group,
                                     custom_properties_group_name=custom_group,
                                     host_service_properties=_host_service_properties, skip_properties=skip_properties,
                                     mapped_properties=mapped_properties)

    def __build_runtime_properties(self, hosts: list):
        # Build Java runtime overrides
        data = (self.group, {'ksql_custom_java_args': self.get_jvm_arguments(self.input_context, self.service, hosts)})
        self.update_inventory(self.inventory, data)

    def _build_service_id(self, service_prop: dict) -> tuple:
        key = "ksql.service.id"
        self.mapped_service_properties.add(key)
        return self.group, {"ksql_service_id": service_prop.get(key)}

    def _build_service_protocol_port(self, service_prop: dict) -> tuple:
        key = "listeners"
        self.mapped_service_properties.add(key)
        listener = service_prop.get(key).split(',')[0]
        parsed_uri = get_listener_details(listener)

        return self.group, {
            "ksql_http_protocol": parsed_uri['scheme'],
            "ksql_listener_port": parsed_uri['port']
        }

    def _build_ksql_internal_replication_property(self, service_prop: dict) -> tuple:
        key1 = "ksql.internal.topic.replicas"
        key2 = "ksql.streams.replication.factor"
        self.mapped_service_properties.add(key1)
        self.mapped_service_properties.add(key2)
        value = service_prop.get(key1)
        if value is not None:
            return self.group, {"ksql_default_internal_replication_factor": int(value)}
        return self.group, {}

    def _build_monitoring_interceptor_property(self, service_prop: dict) -> tuple:
        key = "confluent.monitoring.interceptor.topic"
        self.mapped_service_properties.add(key)
        return self.group, {"ksql_monitoring_interceptors_enabled": key in service_prop}

    def _build_ssl_properties(self, service_prop: dict) -> tuple:
        key = "listeners"
        ksql_listener = service_prop.get(key)

        if ksql_listener.find('https') < 0:
            return self.group, {}

        property_list = ["ssl.truststore.location", "ssl.truststore.password", "ssl.keystore.location",
                         "ssl.keystore.password", "ssl.key.password"]
        for property_key in property_list:
            self.mapped_service_properties.add(property_key)

        property_dict = dict()
        property_dict['ssl_enabled'] = True
        property_dict['ssl_provided_keystore_and_truststore'] = True
        property_dict['ssl_provided_keystore_and_truststore_remote_src'] = True
        property_dict['ksql_truststore_path'] = service_prop.get('ssl.truststore.location')

        if service_prop.get('ssl.truststore.password').startswith("${securepass"):
            property_dict['ssl_truststore_password'] = "<<Value encrypted using secrets protection>>"
        else:
            property_dict['ssl_truststore_password'] = service_prop.get('ssl.truststore.password')

        if service_prop.get('ssl.keystore.password').startswith("${securepass"):
            property_dict['ssl_keystore_store_password'] = "<<Value encrypted using secrets protection>>"
        else:
            property_dict['ssl_keystore_store_password'] = service_prop.get('ssl.keystore.password')

        if service_prop.get('ssl.key.password').startswith("${securepass"):
            property_dict['ssl_keystore_key_password'] = "<<Value encrypted using secrets protection>>"
        else:
            property_dict['ssl_keystore_key_password'] = service_prop.get('ssl.key.password')

        property_dict['ksql_keystore_path'] = service_prop.get('ssl.keystore.location')
        property_dict['ssl_truststore_ca_cert_alias'] = ''

        keystore_aliases = self.get_keystore_alias_names(input_context=self.input_context,
                                                         keystorepass=property_dict['ssl_keystore_store_password'],
                                                         keystorepath=property_dict['ksql_keystore_path'],
                                                         hosts=self.hosts)
        truststore_aliases = self.get_keystore_alias_names(input_context=self.input_context,
                                                           keystorepass=property_dict['ssl_truststore_password'],
                                                           keystorepath=property_dict['ksql_truststore_path'],
                                                           hosts=self.hosts)
        if keystore_aliases:
            # Set the first alias name
            property_dict["ssl_keystore_alias"] = keystore_aliases[0]
        if truststore_aliases:
            property_dict["ssl_truststore_ca_cert_alias"] = truststore_aliases[0]

        return self.group, property_dict

    def _build_mtls_property(self, service_prop: dict) -> tuple:
        key = 'ssl.client.auth'
        self.mapped_service_properties.add(key)
        value = service_prop.get(key)
        if value is not None and value == 'true':
            return "ksql", {'ssl_mutual_auth_enabled': True}
        return self.group, {}

    def _build_authentication_property(self, service_prop: dict) -> tuple:
        key = 'authentication.method'
        self.mapped_service_properties.add(key)
        value = service_prop.get(key)
        if value is not None and value == 'BASIC':
            return self.group, {'ksql_authentication_type': 'basic'}
        return self.group, {}

    def _build_log_streaming_property(self, service_prop: dict) -> tuple:
        key = 'ksql.logging.processing.topic.auto.create'
        self.mapped_service_properties.add(key)
        value = service_prop.get(key)
        if value is not None and value == 'true':
            return self.group, {'ksql_log_streaming_enabled': True}
        return self.group, {}

    def _build_rbac_properties(self, service_prop: dict) -> tuple:
        key1 = 'ksql.security.extension.class'
        if service_prop.get(key1) is None:
            return self.group, {'rbac_enabled': False}
        property_dict = dict()
        key2 = 'public.key.path'
        key3 = 'confluent.metadata.bootstrap.server.urls'
        property_dict['rbac_enabled'] = True
        property_dict['rbac_enabled_public_pem_path'] = service_prop.get(key2)
        self.mapped_service_properties.add(key1)
        self.mapped_service_properties.add(key2)
        self.mapped_service_properties.add(key3)
        return self.group, property_dict

    def _build_ldap_properties(self, service_prop: dict) -> tuple:
        property_dict = dict()
        key = 'confluent.metadata.basic.auth.user.info'
        self.mapped_service_properties.add(key)
        if service_prop.get(key) is not None:
            metadata_user_info = service_prop.get(key)

            if metadata_user_info.startswith("${securepass"):
                property_dict['ksql_ldap_user'] = "<<Value encrypted using secrets protection>>"
                property_dict['ksql_ldap_password'] = "<<Value encrypted using secrets protection>>"
            else:
                property_dict['ksql_ldap_user'] = metadata_user_info.split(':')[0]
                property_dict['ksql_ldap_password'] = metadata_user_info.split(':')[1]

        return self.group, property_dict

    def _build_rocksdb_path(self, service_prop: dict) -> tuple:
        rocksdb_path = self.get_rocksdb_path(self.input_context, self.service, self.hosts)
        return self.group, {"ksql_rocksdb_path": rocksdb_path}

    def _build_telemetry_properties(self, service_prop: dict) -> tuple:
        property_dict = self.build_telemetry_properties(service_prop)
        return self.group, property_dict

    def _build_jmx_properties(self, service_properties: dict) -> tuple:
        monitoring_details = self.get_monitoring_details(self.input_context, self.service, self.hosts, 'KSQL_OPTS')
        service_monitoring_details = dict()

        for key, value in monitoring_details.items():
            service_monitoring_details[f"{self.group}_{key}"] = value

        return self.group, service_monitoring_details

    def _build_log4j_properties(self, service_properties: dict) -> tuple:
        log4j_file = self.get_log_file_path(self.input_context, self.service, self.hosts, "KSQL_LOG4J_OPTS")
        default_log4j_file = "/etc/ksqldb/log4j.properties"
        root_logger, file = self.get_root_logger(self.input_context, self.hosts, log4j_file, default_log4j_file)

        if root_logger is None or file is None:
            return self.group, {'ksql_custom_log4j': False}

        return self.group, {
            'log4j_file': file,
            'ksql_log4j_root_logger': root_logger
        }

    def _build_kerberos_properties(self, service_prop: dict) -> tuple:
        key1 = 'sasl.jaas.config'
        key2 = 'confluent.monitoring.interceptor.sasl.jaas.config'
        self.mapped_service_properties.add(key1)
        self.mapped_service_properties.add(key2)

        sasl_config = ""
        if service_prop.get(key1) is not None:
            sasl_config = service_prop.get(key1)
        elif service_prop.get(key2) is not None:
            sasl_config = service_prop.get(key2)
        else:
            return "all", {}

        try:
            keytab = sasl_config.split('keyTab="')[1].split('"')[0]
            principal = sasl_config.split('principal="')[1].split('"')[0]
        except IndexError as e:
            keytab = ""
            principal = ""
        if keytab != "" or principal != "":
            return self.group, {
                'sasl_protocol': 'kerberos',
                'ksql_kerberos_principal': principal,
                'ksql_kerberos_keytab_path': keytab
            }
        return 'all', {}


class KsqlServicePropertyBaseBuilder60(KsqlServicePropertyBaseBuilder):
    pass


class KsqlServicePropertyBaseBuilder61(KsqlServicePropertyBaseBuilder):
    pass


class KsqlServicePropertyBaseBuilder62(KsqlServicePropertyBaseBuilder):
    pass


class KsqlServicePropertyBaseBuilder70(KsqlServicePropertyBaseBuilder):
    pass


class KsqlServicePropertyBaseBuilder71(KsqlServicePropertyBaseBuilder):
    pass


class KsqlServicePropertyBaseBuilder72(KsqlServicePropertyBaseBuilder):
    pass
