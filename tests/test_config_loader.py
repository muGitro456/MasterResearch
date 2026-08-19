from masterresearch.utils.config_loader import load_yaml


class TestLoadYaml:
    def test_normal_returns_dict(self):
        result = load_yaml('parameters.yaml')
        assert isinstance(result, dict)

    def test_normal_parameters_has_expected_values(self):
        result = load_yaml('parameters.yaml')
        assert result['N'] == 100
        assert result['GENERATION_MAX'] == 200

    def test_normal_methods_keys_are_strings(self):
        result = load_yaml('methods.yaml')
        assert result['1']['name'] == 'MOPSO'
        assert result['6']['name'] == 'MASTER_C'

    def test_normal_topologies_none_value_is_string_not_null(self):
        result = load_yaml('topologies.yaml')
        assert result['0']['name'] == 'None'

    def test_normal_works_from_arbitrary_cwd(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = load_yaml('parameters.yaml')
        assert result['N'] == 100
