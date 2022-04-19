@0xc1776f751066a792;

using Cxx = import "c++.capnp";
$Cxx.namespace("Idl");

using Common = import "common.capnp";

enum BookUpdateType {
	price @0;
	order @1;
}

struct PriceBook {
	instrumentId @0 :Text;
	bids @1 :List(PriceVolume);
	asks @2 :List(PriceVolume);

	struct PriceVolume {
		price @0 :Float64;
		volume @1 :UInt32;
	}
}

struct InstrumentCreated {
	instrumentId @0 :Text;
	tickSize @1 :Float64;
	extraInfo @2 :Text; # json
	priceChangeLimit @3 :Common.PriceChangeLimit;
}

struct InstrumentExpired {
	instrumentId @0 :Text;
	expirationValue @1 :Float64;
}

struct InstrumentPaused {
	instrumentId @0 :Text;
}

struct InstrumentResumed {
	instrumentId @0 :Text;
}

struct InstrumentParametersUpdated {
	instrumentId @0 :Text;
	parameters @1 :Text; # json
}

struct InstrumentStartupData {
	instrumentId @0 :Text;
	lastTradedPrice @1 :Float64;
}

# Info server is special, because we don't use capnp RPC mechanism here
# This is mostly because the info server needs to be fully optimized for
# bulk broadcasting of messages to a lot of clients, which doesn't suit
# capnproto's RPC well in terms of performance overhead

# For info server we just have a raw tcp connection over which we transfer
# messages of type Common.RawMessage
# Each of the Common.RawMessage contains an anypointer that points to:
# From Client to Server:
# - Info.InfoSubscribeRequest
# From Server to Client:
# - Common.GenericReply
# - Info.PriceBook
# - Common.TradeTick
# - Info.InstrumentCreated
# - Info.InstrumentExpired
# - Info.InstrumentPaused
# - Info.InstrumentResumed
# - Info.InstrumentParametersUpdated
# - Info.InstrumentStartupData
# More messages may be added in the future

struct InfoSubscribeRequest {
	requestId @0 :UInt32;
	bookUpdateType @1 :BookUpdateType;
	adminPassword @2 :Text;
}
