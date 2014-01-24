import emzed.utils as utils
import emzed.io as io
import pytest
import emzed.core.config

@pytest.skip
def test_small():

    if not emzed.core.config.global_config.get("metlin_token"):
        raise Exception("please provide EMZED_METLIN_TOKEN variable "\
                        "on commandline for running test")

    t = utils.toTable("m0",[195.0877, 194.07904])
    tn = utils.matchMetlin(t, "m0", ["M"], 30)
    assert len(tn) == 23
    assert len(set(tn.formula__0.values)) == 5
    t = utils.toTable("m0",[195.0877, ])
    tn = utils.matchMetlin(t, "m0", ["M", "M+H"], 30)
    assert len(tn) == 23
    assert len(set(tn.formula__0.values)) == 5

# error in metlin rest service !
@pytest.mark.xfail
def test_large():
    if not emzed.core.config.global_config.get("metlin_token"):
        raise Exception("please provide EMZED_METLIN_TOKEN variable "\
                        "on commandline for running test")

    mz_values = [185.0877 + i +1 for i in range(100)]
    t = utils.toTable("m0", mz_values)
    tn = utils.matchMetlin(t, "m0", ["M", "M+H", "M+2H", "M+3H"], 3)
    assert len(tn) >= 2709, len(tn)


@pytest.skip
def test_handling_of_wrong_answer_from_metlin(path):
    if not emzed.core.config.global_config.get("metlin_token"):
        raise Exception("please provide EMZED_METLIN_TOKEN variable "\
                        "on commandline for running test")


    t = io.loadCSV(path("data/metlin_input.csv"))
    assert len(t) == 2, len(t)
    tn = utils.matchMetlin(t, "mass__0", ["M"], 3)
    assert len(tn) == 12, len(tn)
    assert set(tn.formula__1.values) == set(["C7H14O6", "C13H10N2"])

