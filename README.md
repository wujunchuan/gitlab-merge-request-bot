# Unit test

## 运行所有测试
pytest tests/

## 运行详细模式
pytest tests/test_util.py -v

## 运行特定测试
pytest tests/test_util.py::TestFilterFilesFromDiff::test_filter_single_file -v

## watch mode
ptw -- -s