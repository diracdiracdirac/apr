import json
from web3 import Web3
from utils import (
    init_rosefraxpool, 
    init_nearpad_dex_router,
    init_rosepool,
    init_nearpadpool,
    init_token,
    getAPR,
)

ROSE = Web3.toChecksumAddress("0xdcD6D4e2B3e1D1E1E6Fa8C21C8A323DcbecfF970")
STROSE = Web3.toChecksumAddress("0xe23d2289FBca7De725DC21a13fC096787A85e16F")
PAD = Web3.toChecksumAddress("0x885f8CF6E45bdd3fdcDc644efdcd0AC93880c781")
FRAX = Web3.toChecksumAddress("0xda2585430fef327ad8ee44af8f1f989a2a91a3d2")
DAI = Web3.toChecksumAddress("0xe3520349F477A5F6EB06107066048508498A291b")
USDC = Web3.toChecksumAddress("0xB12BFcA5A55806AaF64E99521918A4bf0fC40802")
USDT = Web3.toChecksumAddress("0x4988a896b1227218e4A686fdE5EabdcAbd91571f")

lpAddresses = {
    "Stables Farm": {
        "deposited_token_address": "0xfF79D5bff48e1C01b722560D6ffDfCe9FC883587",
        "farm_address": "0x52CACa9a2D52b27b28767d3649565774A3B991f3",
        "pool_address": "0xc90dB0d8713414d78523436dC347419164544A3f",
        "this_months_rewards": 450275.00
    },
    "Frax Farm": {
        "deposited_token_address": "0x4463A118A2fB34640ff8eF7Fe1B3abAcd4aC9fB7",
        "farm_address": "0xB9D873cDc15e462f5414CCdFe618a679a47831b4",
        "pool_address": "0xa34315F1ef49392387Dd143f4578083A9Bd33E94",
        "this_months_rewards": 150092.00
    },
    "UST Farm": {
        "deposited_token_address": "0x94A7644E4D9CA0e685226254f88eAdc957D3c263",
        "farm_address": "0x56DE5E2c25828040330CEF45258F3FFBc090777C",
        "pool_address": "0x8fe44f5cce02D5BE44e3446bBc2e8132958d22B8",
        "this_months_rewards": 300184.00
    },
    "ROSE/FRAX PLP Farm": {
        "deposited_token_address": "0xeD4C231b98b474f7cAeCAdD2736e5ebC642ad707",
        "farm_address": "0x1B10bFCd6192edC573ced7Db7c7e403c7FAb8068",
        "this_months_rewards": 225137.00
    },
    "ROSE/PAD PLP Farm": {
        "deposited_token_address": "0xC6C3cc84EabD4643C382C988fA2830657fc70a6B",
        "farm_address": "0x9b2aE7d53099Ec64e2f6df3B4151FFCf7205f788",
        "this_months_rewards": 525321.00
    },
}
data = []
rose_data = []
w3 = Web3(Web3.HTTPProvider("https://mainnet.aurora.dev/"))

# get price of ROSE 
nearpad_dex_router = init_nearpad_dex_router(w3)
rose_frax_price = (nearpad_dex_router.functions.getAmountsOut(10 ** 18, [ROSE, FRAX]).call())[1]
rose_frax_price = float(rose_frax_price) / 10**18
print("ROSE/FRAX Price:", rose_frax_price)
# rose_dai_price = (nearpad_dex_router.functions.getAmountsIn(10 ** 18, [DAI, PAD, ROSE]).call())[1]
# # rose_dai_price = (nearpad_dex_router.functions.getAmountsOut(10 ** 18, [ROSE, PAD, DAI]).call())[1]
# rose_dai_price = float(rose_dai_price) / 10**18
# print("ROSE/DAI Price:", rose_dai_price)
# rose_usdc_price = (nearpad_dex_router.functions.getAmountsIn(10 ** 6, [USDC, PAD, ROSE]).call())[1]
# # rose_usdc_price = (nearpad_dex_router.functions.getAmountsOut(10 ** 18, [ROSE, PAD, USDC]).call())[1]
# # rose_usdc_price = float(rose_usdc_price) / 10**18
# print("ROSE/USDC Price:", rose_usdc_price)
# rose_usdt_price = (nearpad_dex_router.functions.getAmountsOut(10 ** 18, [ROSE, PAD, USDT]).call())[1]
# rose_usdt_price = float(rose_usdt_price) / 10**18
# print("ROSE/USDT Price:", rose_usdt_price)
# roseprice = (rose_frax_price + rose_dai_price + rose_usdc_price + rose_usdt_price) / 4
roseprice = rose_frax_price # temp 
print("ROSE (averaged) price: ", roseprice)

# get tvl of stROSE
rose_contract = init_token(w3, ROSE)
strose_rose_balance_c = rose_contract.functions.balanceOf(STROSE).call()
strose_rose_balance = float(strose_rose_balance_c) / 10**18
strose_tvl = strose_rose_balance * roseprice
strose_tvl = round(strose_tvl) * 10**18

# get price of stRose
strose_contract = init_token(w3, STROSE)
strose_total_supply = strose_contract.functions.totalSupply().call()
strose_total_supply = float(strose_total_supply) / 10**18
print("stRose total supply: ", strose_total_supply)
strose_rose_ratio = strose_rose_balance / strose_total_supply
stroseprice = roseprice * strose_rose_ratio

rose_data.append({
    "price_of_rose": str(roseprice),
    "price_of_strose": str(stroseprice),
    "strose_rose_ratio": str(strose_rose_ratio),
    "strose_tvl": str(strose_tvl),
    "total_rose_staked": str(strose_rose_balance_c)
})

# fetch apr for each farm
for farmName, payload in lpAddresses.items():
    print("Fetching APR for", farmName)

    # get rewards per second for this farm
    rewardsPerSecond = payload["this_months_rewards"] / 30 / 24 / 60 / 60

    farmTvl = 0
    deposited_token = init_token(w3, payload["deposited_token_address"])
    virtualPrice = 0

    # fetch farm balance
    farmBalance = 0
    try:
        farmBalance = deposited_token.functions.balanceOf(payload["farm_address"]).call()
        farmBalanceStr = str(farmBalance)
        print(farmName, "deposits balance:", float(farmBalanceStr[:len(farmBalanceStr)-18]))
    except:
        print("Error fetching farm balance")
        continue

    # calculate virtual price and TVL
    if farmName == "Stables Farm" or farmName == "Frax Farm" or farmName == "UST Farm":
        virtualPrice = roseprice
        # assume LP token = $1
        virtualPrice = 1.0
        farmTvl = farmBalance
    elif farmName == "ROSE/FRAX PLP Farm":
        farmBalance = farmBalance / 10**18
        try:
            rosefraxpool = init_rosefraxpool(w3)
            pool_reserves = rosefraxpool.functions.getReserves().call()
            frax_reserves = round(float(pool_reserves[0]) / 10**18, 0)
            # assume pool is balanced and multiply FRAX reserve by two
            virtualPrice = float(frax_reserves*2) / float(farmBalance)
            farmTvl = int(round(farmBalance * virtualPrice))
            farmTvl = farmTvl * 10**18
        except:
            print("Error getting farm balance for", farmName)
    elif farmName == "ROSE/PAD PLP Farm":
        farmBalance = farmBalance / 10**18
        pool = init_nearpadpool(w3, payload["deposited_token_address"])
        try:
            reserves = pool.functions.getReserves().call()
            reservesRose = float(reserves[1])
            reservesRose = round(reservesRose / 10**18, 0)
            # assupme pool is balanced and multiply ROSE usd value reserves by two
            virtualPrice = (reservesRose*roseprice)*2 / farmBalance
            farmTvl = int(round(farmBalance * virtualPrice))
            farmTvl = farmTvl * 10**18
        except:
            print("Error getting farm balance for", farmName)

    print(farmName, "deposit token virtual price:", virtualPrice)
    
    # format TVL to float for apr calculation
    farmTvl = str(farmTvl)
    farmTvlFloat = float(farmTvl[:len(farmTvl)-18])
    print(farmName, "deposits TVL:", farmTvlFloat)
    
    # calculate APR
    apr_float = getAPR(roseprice, rewardsPerSecond, farmTvlFloat)
    apr = str("{:0.1f}".format(apr_float)) + "%"
    # apr = str(int(round(apr_float))) + "%"

    data.append({
        "name": farmName,
        "deposited_token_address": payload["deposited_token_address"],
        "farm_address": payload["farm_address"],
        "farm_tvl": str(farmTvl),
        "deposited_token_price": str(virtualPrice),
        "rewards_per_second": str(rewardsPerSecond),
        "apr": apr, 
    })

with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

with open('rose.json', 'w', encoding='utf-8') as f:
    json.dump(rose_data, f, ensure_ascii=False, indent=4)
