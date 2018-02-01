const Discord = require("discord.js");// Gets the discord dependancy
const client = new Discord.Client();//Adds the bot as a client

const fs = require('fs');


var isUpdatingText = false; //Is the bot outputing updates into a channel?
var channelForUpdates;  //The channel to update power in
var updateMessageID;  //The specific message to update


var usersList = []; //Stores all users
var powerList = []; //Stores a users power total

var updateRate = 5000;//the rate in ms to run update() at

client.on("ready", () => {  //Runs when the bot first starts

  console.log("NOMIC ONLINE");  //The console message announcing when the bot is ready.
  var t=setInterval(update,updateRate); //This sets the function "Update" to run every x milliseconds 

});

client.on("message", (message) => { //Runs when any message is recived on any channel. Gives the variable message to use.

  if (message.content === '!update') { //Update command. Starts the update process in the channel this command was issues.
    
    isUpdatingText = true; 
    message.channel.send('Starting...').then(message => updateMessageID=message.id);//Sends a message then records that messages id 
    channelForUpdates = message.channel;  //saves the channel the update was posted in

  }
  if (message.content.startsWith("!add")) { //adds a user

    var str = message.content;  //gets the message contents
    var res = str.split(" "); //splits it into commands an args

    if(res.length>1){ //checks if the command has one arg

      if(res[1].startsWith("<@!")){//checks to see if its a @mention or just a string

        var userMarkup = res[1];//gets @mention username
        var userRes = userMarkup.slice(3,-1);//removes @mention markup to get userID
        client.fetchUser(userRes).then(userData => usersList[usersList.length] = userData.username);//Adds user to the users array

        if(usersList.length>powerList.length){//checks to make sure the user was added properly 

          powerList[powerList.length] = 0;//adds a power level for that user
          message.channel.send("User added");//output to channel

        }else{

          message.channel.send("Error: NO");//In case the user was not added

        }
        

      }else{//if a string username

        usersList[usersList.length] = res[1];//makes user
        powerList[powerList.length] = 0;//gives power
        message.channel.send("User "+ res[1] +" added");//output to channel

      }

      


    }else{//if no second arg
      message.channel.send("Error: Missing Username. !add username");//output to channel
    }
  }

  if (message.content.startsWith("!remove")) {//removes a user

    var str = message.content;//gets message
    var res = str.split(" ");//spits it into args

    if(res.length>1){//checks to see if there are 1 or more args

      var index = usersList.lastIndexOf(res[1]);//finds that user

      if(index != -1){//check to see if that user was found
        usersList.splice(index,1);//removes their user entry
        powerList.splice(index,1);//removes their power level
        message.channel.send("User "+res[1]+" removed");

      }else{//user was not found

        message.channel.send("Error: user "+res[1]+" not found");

      }
    }else{//No args in command

      message.channel.send("Error: Missing Username. !remove username");

    }
  }


});

function update(){//Made to update every x seconds

  addPower();
    
    if(isUpdatingText){//makes sure !update has been sent. Renders the !update post

      var updateString = "";//sets the string to blank

      for (i = 0; i < usersList.length; i++) { //for each user

       updateString+= usersList[i] + ": "+powerList[i]+"W \n";//Adds a user to the !update post. \n adds an new line to the post

      }

      channelForUpdates.fetchMessage(updateMessageID)
      .then(message =>message.edit(updateString)).catch(console.error);//this finds and updates the original post

    }   

    
    saveData();


}

function addPower(){//adds power to the users

  for (i = 0; i < powerList.length; i++) { //for each power list entry

    powerList[i]+=updateRate/1000;  //Uses the update rate to set power growth at 1W per second

   }
}

function saveData(){

  fs.writeFile('/data/userData.txt', usersList, (err) => {  
    // throws an error, you could also catch it here
    if (err) throw err;
    // success case, the file was saved
});
fs.writeFile('/data/powerData.txt', powerList, (err) => {  
  // throws an error, you could also catch it here
  if (err) throw err;
  // success case, the file was saved
});
var updateStuff = [isUpdatingText,channelForUpdates,updateMessageID];
fs.writeFile('/data/updateData.txt', updateStuff, (err) => {  
  // throws an error, you could also catch it here
  if (err) throw err;
  // success case, the file was saved
});

}

client.login("Mzc3NDg2ODk3NjQ1MDkyODY2.DVJV5Q.E5dAeB3OODC8PUvzpiFKYGoVKkw");//The bot to log into. The string is the bots token.