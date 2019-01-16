using System;
using System.IO;
using System.Net.Http;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using System.Text.RegularExpressions;
using System.Threading;
using PokeBotC;

namespace PokeBotTests {
	[TestClass]
	public class ClientIntegrationTests {
		[TestMethod]
		public void ClientConnectsToServer() {
			// TODO This test fails to log in to the server and I don't know why
			using (StringWriter sw = new StringWriter()) {
				Console.SetOut(sw);
				var bot = new Client("pokebot_training_1", "password");

				// This regex looks hideous but it works so I'm not gonna touch it anymore
				Regex rx = new Regex(@"### opened ###$\npokebot_train_1 << \|updateuser\|Guest(.+)$\n\|formats(.+)$\npokebot_train_1 << \|challstr(.+)$\npokebot_train_1 >> \|/trn(.+)$\npokebot_train_1 << \|updatesearch\|\{""searching"":\[\],""games"":null\}\npokebot_train_1 << \|updateuser\|pokebot_train_1(.+)$\npokebot_train_1 << \|updatesearch\|\{""searching"":\[\],""games"":null\}\npokebot_train_1 << \|updatechallenges\|\{""challengesFrom"":\{\},""challengeTo"":null\}\n### closed ###\n");

				// Run the client for five seconds to give it some time to connect and log in
				bot.Run(cycles: 5);
				
				Assert.AreEqual<String>(rx.Match(sw.ToString()).Value, sw.ToString());
			}
		}
	}
}
