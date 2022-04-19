@0x839ac922482c3c3f;

using Cxx = import "c++.capnp";
$Cxx.namespace("Idl");

interface HeartBeat {
	ping @0 ();
}

enum Side {
	bid @0;
	ask @1;
}

enum Action {
	buy @0;
	sell @1;
}

struct InstrumentPosition {
	instrumentId @0 :Text;
	position @1 :Int64;
	cash @2 :Float64;
}

struct Positions {
	basedOnTradeId @0 :UInt64;
	positions @1 :List(InstrumentPosition);
}

struct Order {
	instrumentId @0 :Text;
	orderId @1 :UInt64;
	price @2 :Float64;
	volume @3 :UInt32;
	side @4 :Side;
}

struct SingleSidedBooking {
	tradeId @0 :UInt64;
	timestamp @1 :Int64;
	username @2 :Text;
	instrumentId @3 :Text;
	price @4 :Float64;
	volume @5 :UInt32;
	action @6 :Action;
}

struct TradeTick {
	tradeId @0 :UInt64;
	timestamp @1 :Int64;
	instrumentId @2 :Text;
	price @3 :Float64;
	volume @4 :UInt32;
	aggressorSide @5 :Side;
	buyer @6 :Text;
	seller @7 :Text;
}

struct RawMessage {
	type @0 :UInt64;
	msg @1 :AnyPointer;
}

struct GenericReply {
	requestId @0 :UInt32;
	errorMessage @1 :Text;
}

struct PriceChangeLimit {
	absoluteChange @0 :Float64;
	relativeChange @1 :Float64;
}
