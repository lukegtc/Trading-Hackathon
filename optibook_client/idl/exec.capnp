@0x85150b117366d14b;

using Cxx = import "c++.capnp";
$Cxx.namespace("Idl");

using Common = import "common.capnp";

enum OrderType {
	limit @0;
	ioc @1;
}

struct Trade {
	tradeId @0 :UInt64;
	timestamp @1 :Int64;
	instrumentId @2 :Text;
	orderId @3 : UInt64;
	price @4 :Float64;
	volume @5 :UInt32;
	side @6 :Common.Side;
}

interface ExecPortal {
	login @0 (username :Text, password :Text, callbackInterface :ExecFeed) -> (exec :Exec, positions :Common.Positions);
	adminLogin @1 (username :Text, password :Text, adminPassword :Text, callbackInterface :ExecFeed) -> (exec :Exec, positions :Common.Positions);

	interface Exec {
		insertOrder @0 (instrumentId :Text, price :Float64, volume :UInt32, side :Common.Side, orderType :OrderType) -> (orderId :UInt64);
		amendOrder @1 (instrumentId :Text, orderId :UInt64, volume :UInt32) -> (success :Bool);
		deleteOrder @2 (instrumentId :Text, orderId :UInt64) -> (success :Bool);
		deleteOrders @3 (instrumentId :Text);
		updateInstrumentParameters @4 (instrumentId :Text, parameters :Text);
	}

	interface ExecFeed extends (Common.HeartBeat) {
		onOrderUpdate @0 (order :Common.Order);
		onTrade @1 (trade :Trade);
		onSingleSidedBooking @2 (ssb :Common.SingleSidedBooking);
		onForcedDisconnect @3 (reason :Text);
		onNotification @4 (source :Text, msg :Text);
	}
}
