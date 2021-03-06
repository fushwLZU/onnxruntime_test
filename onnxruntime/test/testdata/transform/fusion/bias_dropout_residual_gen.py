import onnx
from onnx import helper
from onnx import TensorProto, OperatorSetIdProto

# inputs/outputs
A = helper.make_tensor_value_info('A', TensorProto.FLOAT, ['unk_1', 'unk_2', 3072])
B = helper.make_tensor_value_info('B', TensorProto.FLOAT, [3072])
R = helper.make_tensor_value_info('R', TensorProto.FLOAT, ['unk_1', 'unk_2', 3072])
C = helper.make_tensor_value_info('C', TensorProto.FLOAT, ['unk_1', 'unk_2', 3072])
mask = helper.make_tensor_value_info('mask', TensorProto.BOOL, ['unk_1', 'unk_2', 3072])

# initializers
ratio = helper.make_tensor('ratio_const', TensorProto.FLOAT, [], [0.8])
training_mode = helper.make_tensor('training_mode', TensorProto.BOOL, [], [1])

opsets = []
onnxdomain = OperatorSetIdProto()
onnxdomain.version = 12
onnxdomain.domain = "" # The empty string ("") or absence of this field implies the operator set that is defined as part of the ONNX specification.
opsets.append(onnxdomain)

kwargs={}
kwargs['opset_imports'] = opsets

# Create the model (ModelProto)
bias = helper.make_node("Add", ["A", "B"], ["add0_out"], "add0")
dropout_12 = helper.make_node("Dropout", ["add0_out", "ratio_const", "training_mode"], ["C", "mask"], "dropout0")

graph = helper.make_graph(
    [bias, dropout_12],
    "Bias_Dropout_Fusion",  #name
    [A, B],
    [C],
    [ratio, training_mode])

model = helper.make_model(graph, producer_name='onnx-example', **kwargs)
onnx.save(model, 'bias_dropout_fusion1.onnx')

# Create the model (ModelProto)
bias = helper.make_node("Add", ["B", "A"], ["add0_out"], "add0")
dropout_12 = helper.make_node("Dropout", ["add0_out", "ratio_const", "training_mode"], ["C", "mask"], "dropout0")

graph = helper.make_graph(
    [bias, dropout_12],
    "Bias_Dropout_Fusion",  #name
    [A, B],
    [C],
    [ratio, training_mode])

model = helper.make_model(graph, producer_name='onnx-example', **kwargs)
onnx.save(model, 'bias_dropout_fusion2.onnx')


# Create the model (ModelProto)
bias = helper.make_node("Add", ["A", "B"], ["add0_out"], "add0")
dropout_12 = helper.make_node("Dropout", ["add0_out", "ratio_const", "training_mode"], ["dropout_out", "mask"], "dropout0")
residual = helper.make_node("Add", ["dropout_out", "R"], ["C"], "add1")

graph = helper.make_graph(
    [bias, dropout_12, residual],
    "Bias_Dropout_Fusion",  #name
    [A, B, R],
    [C],
    [ratio, training_mode])

model = helper.make_model(graph, producer_name='onnx-example', **kwargs)
onnx.save(model, 'bias_dropout_residual_fusion1.onnx')

# Create the model (ModelProto)
bias = helper.make_node("Add", ["B", "A"], ["add0_out"], "add0")
dropout_12 = helper.make_node("Dropout", ["add0_out", "ratio_const", "training_mode"], ["dropout_out", "mask"], "dropout0")
residual = helper.make_node("Add", ["R", "dropout_out"], ["C"], "add1")

graph = helper.make_graph(
    [bias, dropout_12, residual],
    "Bias_Dropout_Fusion",  #name
    [A, B, R],
    [C],
    [ratio, training_mode])

model = helper.make_model(graph, producer_name='onnx-example', **kwargs)
onnx.save(model, 'bias_dropout_residual_fusion2.onnx')

# Create the model (ModelProto)
R_mismatch = helper.make_tensor_value_info('R', TensorProto.FLOAT, [3072])

bias = helper.make_node("Add", ["B", "A"], ["add0_out"], "add0")
dropout_12 = helper.make_node("Dropout", ["add0_out", "ratio_const", "training_mode"], ["dropout_out", "mask"], "dropout0")
residual = helper.make_node("Add", ["R", "dropout_out"], ["C"], "add1")

graph = helper.make_graph(
    [bias, dropout_12, residual],
    "Bias_Dropout_Fusion",  #name
    [A, B, R_mismatch],
    [C],
    [ratio, training_mode])

model = helper.make_model(graph, producer_name='onnx-example', **kwargs)
onnx.save(model, 'bias_dropout_residual_fusion_mismatch.onnx')

# If the Dropout output 0 is also a graph output, the residual Add shouldn't be fused.
# Create the model (ModelProto)
bias = helper.make_node("Add", ["B", "A"], ["add0_out"], "add0")
dropout_12 = helper.make_node("Dropout", ["add0_out", "ratio_const", "training_mode"], ["dropout_out", "mask"], "dropout0")
residual = helper.make_node("Add", ["R", "dropout_out"], ["C"], "add1")

D = helper.make_tensor_value_info('dropout_out', TensorProto.FLOAT, ['unk_1', 'unk_2', 3072])

graph = helper.make_graph(
    [bias, dropout_12, residual],
    "Bias_Dropout_Fusion",  #name
    [A, B, R],
    [C, D],
    [ratio, training_mode])

model = helper.make_model(graph, producer_name='onnx-example', **kwargs)
onnx.save(model, 'bias_dropout_residual_fusion_multiple_consumers1.onnx')

# If the Dropout has multiple consumers of output 0, the residual Add shouldn't be fused.
# Create the model (ModelProto)
D = helper.make_tensor_value_info('D', TensorProto.FLOAT, ['unk_1', 'unk_2', 3072])
bias = helper.make_node("Add", ["B", "A"], ["add0_out"], "add0")
dropout_12 = helper.make_node("Dropout", ["add0_out", "ratio_const", "training_mode"], ["dropout_out", "mask"], "dropout0")
residual = helper.make_node("Add", ["R", "dropout_out"], ["C"], "add1")
identity = helper.make_node("Identity", ["dropout_out"], ["D"], "identity")

graph = helper.make_graph(
    [bias, dropout_12, residual, identity],
    "Bias_Dropout_Fusion",  #name
    [A, B, R],
    [C, D],
    [ratio, training_mode])

model = helper.make_model(graph, producer_name='onnx-example', **kwargs)
onnx.save(model, 'bias_dropout_residual_fusion_multiple_consumers2.onnx')


# Create the model (ModelProto)
A2 = helper.make_tensor_value_info('A2', TensorProto.FLOAT, ['unk_1', 'unk_2', 3072])

bias = helper.make_node("Add", ["A", "A2"], ["add0_out"], "add0")
dropout_12 = helper.make_node("Dropout", ["add0_out", "ratio_const", "training_mode"], ["C", "mask"], "dropout0")

graph = helper.make_graph(
    [bias, dropout_12],
    "Bias_Dropout_Fusion",  #name
    [A, A2],
    [C],
    [ratio, training_mode])

model = helper.make_model(graph, producer_name='onnx-example', **kwargs)
onnx.save(model, 'bias_dropout_same_shape_fusion.onnx')

# Create the model (ModelProto)
bias = helper.make_node("Add", ["A", "A2"], ["add0_out"], "add0")
dropout_12 = helper.make_node("Dropout", ["add0_out", "ratio_const", "training_mode"], ["dropout_out", "mask"], "dropout0")
residual = helper.make_node("Add", ["dropout_out", "R"], ["C"], "add1")

graph = helper.make_graph(
    [bias, dropout_12, residual],
    "Bias_Dropout_Fusion",  #name
    [A, A2, R],
    [C],
    [ratio, training_mode])

model = helper.make_model(graph, producer_name='onnx-example', **kwargs)
onnx.save(model, 'bias_dropout_residual_same_shape_fusion.onnx')


# Create the model (ModelProto)
A_unk = helper.make_tensor_value_info('A_unk', TensorProto.FLOAT, ['unk_1', 'unk_2', 'unk_3'])
B_unk = helper.make_tensor_value_info('B_unk', TensorProto.FLOAT, ['unk_3'])
C_unk = helper.make_tensor_value_info('C_unk', TensorProto.FLOAT, ['unk_1', 'unk_2', 'unk_3'])

bias = helper.make_node("Add", ["A_unk", "B_unk"], ["add0_out"], "add0")
dropout_12 = helper.make_node("Dropout", ["add0_out", "ratio_const", "training_mode"], ["C_unk", "mask"], "dropout0")

graph = helper.make_graph(
    [bias, dropout_12],
    "Bias_Dropout_Fusion",  #name
    [A_unk, B_unk],
    [C_unk],
    [ratio, training_mode])

model = helper.make_model(graph, producer_name='onnx-example', **kwargs)
onnx.save(model, 'bias_dropout_fusion_dim_is_param.onnx')

# Create the model (ModelProto)
R_unk = helper.make_tensor_value_info('R_unk', TensorProto.FLOAT, ['unk_1', 'unk_2', 'unk_3'])

bias = helper.make_node("Add", ["A_unk", "B_unk"], ["add0_out"], "add0")
dropout_12 = helper.make_node("Dropout", ["add0_out", "ratio_const", "training_mode"], ["dropout_out", "mask"], "dropout0")
residual = helper.make_node("Add", ["dropout_out", "R_unk"], ["C_unk"], "add1")

graph = helper.make_graph(
    [bias, dropout_12, residual],
    "Bias_Dropout_Fusion",  #name
    [A_unk, B_unk, R_unk],
    [C_unk],
    [ratio, training_mode])

model = helper.make_model(graph, producer_name='onnx-example', **kwargs)
onnx.save(model, 'bias_dropout_residual_fusion_dim_is_param.onnx')

# Create the model (ModelProto)
A_unk2 = helper.make_tensor_value_info('A_unk2', TensorProto.FLOAT, ['unk_1', 'unk_2', 'unk_3'])

bias = helper.make_node("Add", ["A_unk", "A_unk2"], ["add0_out"], "add0")
dropout_12 = helper.make_node("Dropout", ["add0_out", "ratio_const", "training_mode"], ["C_unk", "mask"], "dropout0")

graph = helper.make_graph(
    [bias, dropout_12],
    "Bias_Dropout_Fusion",  #name
    [A_unk, A_unk2],
    [C_unk],
    [ratio, training_mode])

model = helper.make_model(graph, producer_name='onnx-example', **kwargs)
onnx.save(model, 'bias_dropout_same_shape_fusion_dim_is_param.onnx')

# Create the model (ModelProto)
bias = helper.make_node("Add", ["A_unk", "A_unk2"], ["add0_out"], "add0")
dropout_12 = helper.make_node("Dropout", ["add0_out", "ratio_const", "training_mode"], ["dropout_out", "mask"], "dropout0")
residual = helper.make_node("Add", ["dropout_out", "R_unk"], ["C_unk"], "add1")

graph = helper.make_graph(
    [bias, dropout_12, residual],
    "Bias_Dropout_Fusion",  #name
    [A_unk, A_unk2, R_unk],
    [C_unk],
    [ratio, training_mode])

model = helper.make_model(graph, producer_name='onnx-example', **kwargs)
onnx.save(model, 'bias_dropout_residual_same_shape_fusion_dim_is_param.onnx')
