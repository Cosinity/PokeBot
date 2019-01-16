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
		public static bool verbose = true;
		public static HttpClient httpClient = new HttpClient();
	}

	public class Client {
		private readonly WebSocket wsCLient;
		private readonly HttpClient httpClient;
		private readonly string username;
		private readonly string password;
		private int rqid;

		public Client(string name, string pass, string server = "ws://sim.smogon.com:8000/showdown/websocket") {
			wsCLient = new WebSocket(server);
			username = name;
			password = pass;
			rqid = -1;
			
			wsCLient.OnOpen += (sender, e) =>
			{
				Console.WriteLine("### opened ###");
			};
			wsCLient.OnClose += (sender, e) =>
			{
				Console.WriteLine("### closed ###");
			};
			wsCLient.OnError += (sender, e) =>
			{
				Console.WriteLine(e.Message);
			};

			wsCLient.OnMessage += (sender, e) => {
				string msg = e.Data;
				if (Globals.verbose) {
					Console.WriteLine("{0} << {1}", this.username, msg);
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

					// Check if there was an error in the response and handle it
					else if (msg.Contains("|error|")) {
						var errIdx = msg.IndexOf("|error|") + 7;
						var curErr = msg.Substring(errIdx);
						Console.WriteLine("Error from server: {0}", curErr);

						// If we made an invalid choice, try again
						if (curErr.Contains("Invalid choice")) {
							// TODO (var action, var actIdx) = this.GetAction();
							// TODO this.send(String.Format("{0}|/choose {1} {2}|{3}", room, action, actIdx, this.rqid);
						}
					}

					// If it's any other type of message (usually a turn upkeep message), pass it to the state to update accordingly
					else {
						// TODO this.curState.update(msg);
					}
				}
			};
		}

		/// <summary>
		/// Runs the client for the specified amount of time
		/// </summary>
		/// <param name="cycles">OPTIONAL How many cycles the client should run for. If this is not supplied, client will run indefinitely.</param>
		/// <param name="timeType">OPTIONAL What type of cycle the client will use. If this parameter is "iterations" then the client will run for the specified number of battles.
		/// Otherwise, it runs for the specified number of seconds.</param>
		public void Run(int cycles = -1, string timeType = "time") {
			using (var ws = this.wsCLient) {
				this.wsCLient.Connect();
				if (cycles < 0) {
					while (true) { }
				} else if (timeType == "iterations") {
					// TODO fill this out
				} else {
					Thread.Sleep(cycles * 1000);
				}
			}
		}

		private void Send(string msg) {
			if (Globals.verbose) {
				Console.WriteLine("{0} >> {1}", this.username, msg);
			}
			this.wsCLient.Send(msg);
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
			var resp = await Globals.httpClient.PostAsync("http://play.pokemonshowdown.com/action.php", content);

			var responseString = (await resp.Content.ReadAsStringAsync()).Substring(1);

			var respObj = JsonConvert.DeserializeObject<Newtonsoft.Json.Linq.JToken>(responseString);
			var assertion = (String)respObj["assertion"];
			this.Send(String.Format("|/trn {0},0,{1}", this.username, assertion));
		}
	}

	class Run {
		static void Main(string[] args) {
			foreach (string s in args) {
				if (s.Contains("verbose")) {
					Globals.verbose = Convert.ToBoolean(s.Substring(s.IndexOf(':')+1));
				}
			}

			var bot1 = new Client("pokebot_train_1", "password");
			bot1.Run();
		}
	}
}
