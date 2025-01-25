
try:
    import openttd.tile
except ImportError:
    import openttd

Tile=openttd.tile.Tile
Dir=openttd.tile.Dir
Turn=openttd.tile.Turn

def test_tile_dir_ops():
    t = Tile(10,20)

    tn = t+Dir.N
    assert tn.xy == (9,19)
    tn = t+Dir.NE
    assert tn.xy == (9,20)
    tn = t+Dir.E
    assert tn.xy == (9,21)
    tn = t+Dir.SE
    assert tn.xy == (10,21)
    tn = t+Dir.S
    assert tn.xy == (11,21)
    tn = t+Dir.SW
    assert tn.xy == (11,20)
    tn = t+Dir.W
    assert tn.xy == (11,19)
    tn = t+Dir.NW
    assert tn.xy == (10,19)

    assert t.xy == (10,20)

def test_tile_turn_ops():
    d=Dir.N
    assert d+Turn.R==Dir.NE
    assert d+Turn.RR==Dir.E
    assert d+Turn.L==Dir.NW
    assert d+Turn.LL==Dir.W
    assert d+Turn.B==Dir.S
    assert d==Dir.N

    assert Turn.S+Turn.L==Turn.L
    assert Turn.L+Turn.L==Turn.LL
    assert Turn.R+Turn.L==Turn.S
    assert Turn.RR+Turn.L==Turn.R
    assert Turn.B+Turn.LL==Turn.RR
