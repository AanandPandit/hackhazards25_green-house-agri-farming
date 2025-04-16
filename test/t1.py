from fluvio import ConsumerConfig

config = ConsumerConfig()
config.smartmodule(name="uppercase")

stream = consumer.stream_with_config(Offset.latest(), config)
