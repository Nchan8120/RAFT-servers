# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: heartbeat_service.proto
# Protobuf Python Version: 4.25.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x17heartbeat_service.proto\x12\x0bviewservice\x1a\x1bgoogle/protobuf/empty.proto\".\n\x10HeartbeatRequest\x12\x1a\n\x12service_identifier\x18\x01 \x01(\t\"$\n\x11HeartbeatResponse\x12\x0f\n\x07message\x18\x01 \x01(\t\".\n\x14\x41\x64\x64\x42\x61\x63kupStubRequest\x12\x16\n\x0e\x62\x61\x63kup_address\x18\x01 \x01(\t\"1\n\x17RemoveBackupStubRequest\x12\x16\n\x0e\x62\x61\x63kup_address\x18\x01 \x01(\t2\xef\x01\n\x0bViewService\x12\x42\n\tHeartbeat\x12\x1d.viewservice.HeartbeatRequest\x1a\x16.google.protobuf.Empty\x12J\n\rAddBackupStub\x12!.viewservice.AddBackupStubRequest\x1a\x16.google.protobuf.Empty\x12P\n\x10RemoveBackupStub\x12$.viewservice.RemoveBackupStubRequest\x1a\x16.google.protobuf.Emptyb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'heartbeat_service_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  DESCRIPTOR._options = None
  _globals['_HEARTBEATREQUEST']._serialized_start=69
  _globals['_HEARTBEATREQUEST']._serialized_end=115
  _globals['_HEARTBEATRESPONSE']._serialized_start=117
  _globals['_HEARTBEATRESPONSE']._serialized_end=153
  _globals['_ADDBACKUPSTUBREQUEST']._serialized_start=155
  _globals['_ADDBACKUPSTUBREQUEST']._serialized_end=201
  _globals['_REMOVEBACKUPSTUBREQUEST']._serialized_start=203
  _globals['_REMOVEBACKUPSTUBREQUEST']._serialized_end=252
  _globals['_VIEWSERVICE']._serialized_start=255
  _globals['_VIEWSERVICE']._serialized_end=494
# @@protoc_insertion_point(module_scope)
