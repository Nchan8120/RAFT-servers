# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: replication.proto
# Protobuf Python Version: 4.25.3
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x11replication.proto\x12\x0breplication\"\x88\x01\n\x14\x41ppendEntriesRequest\x12\x0c\n\x04term\x18\x01 \x01(\x05\x12\x10\n\x08leaderId\x18\x02 \x01(\x05\x12\x14\n\x0cprevLogIndex\x18\x03 \x01(\x05\x12\x13\n\x0bprevLogTerm\x18\x04 \x01(\x05\x12\x14\n\x0cleaderCommit\x18\x05 \x01(\x05\x12\x0f\n\x07\x65ntries\x18\x06 \x03(\t\"6\n\x15\x41ppendEntriesResponse\x12\x0c\n\x04term\x18\x01 \x01(\x05\x12\x0f\n\x07success\x18\x02 \x01(\x08\"*\n\x0cWriteRequest\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t\"\x1c\n\rWriteResponse\x12\x0b\n\x03\x61\x63k\x18\x01 \x01(\t\"g\n\x12RequestVoteRequest\x12\x0c\n\x04term\x18\x01 \x01(\x05\x12\x14\n\x0c\x63\x61ndidate_id\x18\x02 \x01(\x05\x12\x16\n\x0elast_log_index\x18\x03 \x01(\x05\x12\x15\n\rlast_log_term\x18\x04 \x01(\x05\"9\n\x13RequestVoteResponse\x12\x0c\n\x04term\x18\x01 \x01(\x05\x12\x14\n\x0cvote_granted\x18\x02 \x01(\x08\x32\xf4\x01\n\x08Sequence\x12V\n\rAppendEntries\x12!.replication.AppendEntriesRequest\x1a\".replication.AppendEntriesResponse\x12>\n\x05Write\x12\x19.replication.WriteRequest\x1a\x1a.replication.WriteResponse\x12P\n\x0bRequestVote\x12\x1f.replication.RequestVoteRequest\x1a .replication.RequestVoteResponseb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'replication_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  DESCRIPTOR._options = None
  _globals['_APPENDENTRIESREQUEST']._serialized_start=35
  _globals['_APPENDENTRIESREQUEST']._serialized_end=171
  _globals['_APPENDENTRIESRESPONSE']._serialized_start=173
  _globals['_APPENDENTRIESRESPONSE']._serialized_end=227
  _globals['_WRITEREQUEST']._serialized_start=229
  _globals['_WRITEREQUEST']._serialized_end=271
  _globals['_WRITERESPONSE']._serialized_start=273
  _globals['_WRITERESPONSE']._serialized_end=301
  _globals['_REQUESTVOTEREQUEST']._serialized_start=303
  _globals['_REQUESTVOTEREQUEST']._serialized_end=406
  _globals['_REQUESTVOTERESPONSE']._serialized_start=408
  _globals['_REQUESTVOTERESPONSE']._serialized_end=465
  _globals['_SEQUENCE']._serialized_start=468
  _globals['_SEQUENCE']._serialized_end=712
# @@protoc_insertion_point(module_scope)
