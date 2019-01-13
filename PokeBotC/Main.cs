using System;
using System.Collections.Generic;
using System.Threading;
using System.Net.Http;
using WebSocketSharp;
using Newtonsoft.Json;
using System.Diagnostics;

namespace PokeBotC
{
	public static class Globals {
		public static bool verbose = false;
	}

	class Bot {
		private readonly WebSocket client;
		private readonly HttpClient httpClient;
		private readonly string username;
		private readonly string password;
		private int rqid;

		public Bot(string name, string pass, HttpClient httpC, string server = "ws://sim.smogon.com:8000/showdown/websocket") {
			client = new WebSocket(server);
			httpClient = httpC;
			username = name;
			password = pass;
			rqid = -1;
			
			client.OnOpen += (sender, e) =>
			{
				Debug.WriteLine("### opened ###");
			};
			client.OnClose += (sender, e) =>
			{
				Debug.WriteLine("### closed ###");
			};
			client.OnError += (sender, e) =>
			{
				Debug.WriteLine(e.Message);
			};

			client.OnMessage += (sender, e) => {
				string msg = e.Data;
				if (Globals.verbose) {
					Debug.WriteLine("{0} << {1}", this.username, msg);
				}
				
				// We've just connected to the server and it's given us the challenge string to log in
				if (msg.Contains("|challstr|")) {
					string challstr = msg.Substring(10);
					this.Login(challstr);
				}

				// Handle all messages seen in a battle
				else if (msg.Contains("battle")) {
					var room = msg.Substring(1, msg.IndexOf('|') - 1);

					// The server is requesting something
					if (msg.Contains("|request|")) {
						var req_idx = msg.IndexOf("|request|") + 9;
						var cur_req = msg.Substring(req_idx);

						if (!cur_req.IsNullOrEmpty()) {
							var curPlayerState = JsonConvert.DeserializeObject<Newtonsoft.Json.Linq.JToken>(cur_req);
							this.rqid = (int)curPlayerState["rqid"];

							if (curPlayerState["active"] != null || curPlayerState["forceSwitch"] != null) {
								// TODO this.curState.UpdateFromRequest(curPlayerState);
								// TODO (var action, var actIdx) = this.GetAction();
								// TODO this.send(String.Format("{0}|/choose {1} {2}|{3}", room, action, actIdx, this.rqid);
							}

							else if (curPlayerState["teamPreview"] != null) {
								// TODO this.curState.UpdateFromRequest(curPlayerState);
								// TODO var teamOrder = this.get_lead();
								// this.send(String.Format("{0}|/team {1}|{2}", room, teamOrder, this.rqid);
							}
						}
					}
				}
			};
		}

		public void Run() {
			using (var ws = this.client) {
				this.client.Connect();
				while (true) { }
			}
		}

		private void Send(string msg) {
			if (Globals.verbose) {
				Debug.WriteLine("{0} >> {1}", this.username, msg);
			}
			this.client.Send(msg);
		}

		async private void Login(string challstr) {
			var data = new Dictionary<String, String> {
				{"act", "login"},
				{"name", this.username},
				{"pass", this.password},
				{"challengekeyid", challstr[0].ToString()},
				{"challenge", challstr.Substring(2)}
			};

			var content = new FormUrlEncodedContent(data);
			var resp = await this.httpClient.PostAsync("http://play.pokemonshowdown.com/action.php", content);

			var responseString = (await resp.Content.ReadAsStringAsync()).Substring(1);

			var respObj = JsonConvert.DeserializeObject<Newtonsoft.Json.Linq.JToken>(responseString);
			var assertion = (String)respObj["assertion"];
			this.Send(String.Format("|/trn {0},0,{1}", this.username, assertion));
		}
	}

	class Run {
		private static readonly HttpClient httpClient = new HttpClient();

		static void Main(string[] args) {
			foreach (string s in args) {
				if (s.Contains("verbose")) {
					Globals.verbose = Convert.ToBoolean(s.Substring(s.IndexOf(':')+1));
				}
			}
		}
	}
}
