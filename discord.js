const Discord = require('discord.js');
const fs = require('fs');

// Initialize the Discord client with partials to handle reactions on uncached messages
const client = new Discord.Client({ partials: ['MESSAGE', 'CHANNEL', 'REACTION'] });

// Load configuration from config.json
let config = JSON.parse(fs.readFileSync('config.json', 'utf8'));

// Log when the bot is ready
client.on('ready', () => {
    console.log(`Logged in as ${client.user.tag}!`);
});

// Handle incoming messages
client.on('message', message => {
    // Ignore messages from bots or outside guilds
    if (!message.guild || message.author.bot) return;

    // Check if the message starts with the prefix '!'
    if (message.content.startsWith('!')) {
        const args = message.content.slice(1).trim().split(/ +/);
        const command = args.shift().toLowerCase();

        // Moderation Commands
        if (command === 'kick') {
            if (!message.member.hasPermission('KICK_MEMBERS')) return message.reply('You need Kick Members permission.');
            const user = message.mentions.users.first();
            if (!user) return message.reply('Please mention a user to kick.');
            const reason = args.slice(1).join(' ') || 'No reason provided';
            const member = message.guild.members.cache.get(user.id);
            member.kick(reason).then(() => {
                message.reply(`${user.tag} has been kicked.`);
                logAction('Kick', user, message.author, reason, message.guild);
            }).catch(err => {
                message.reply('I was unable to kick the member. Check my permissions.');
                console.error(err);
            });
        } else if (command === 'ban') {
            if (!message.member.hasPermission('BAN_MEMBERS')) return message.reply('You need Ban Members permission.');
            const user = message.mentions.users.first();
            if (!user) return message.reply('Please mention a user to ban.');
            const reason = args.slice(1).join(' ') || 'No reason provided';
            const member = message.guild.members.cache.get(user.id);
            member.ban({ reason }).then(() => {
                message.reply(`${user.tag} has been banned.`);
                logAction('Ban', user, message.author, reason, message.guild);
            }).catch(err => {
                message.reply('I was unable to ban the member. Check my permissions.');
                console.error(err);
            });
        } else if (command === 'mute') {
            if (!message.member.hasPermission('MANAGE_ROLES')) return message.reply('You need Manage Roles permission.');
            const user = message.mentions.users.first();
            if (!user) return message.reply('Please mention a user to mute.');
            const settings = config[message.guild.id];
            if (!settings || !settings.muteRole) return message.reply('Mute role not set. Use !setmute @role.');
            const muteRole = message.guild.roles.cache.get(settings.muteRole);
            if (!muteRole) return message.reply('Mute role not found.');
            const member = message.guild.members.cache.get(user.id);
            member.roles.add(muteRole).then(() => {
                message.reply(`${user.tag} has been muted.`);
                logAction('Mute', user, message.author, 'Muted', message.guild);
            }).catch(err => {
                message.reply('I was unable to mute the member. Check my permissions.');
                console.error(err);
            });
        } else if (command === 'unmute') {
            if (!message.member.hasPermission('MANAGE_ROLES')) return message.reply('You need Manage Roles permission.');
            const user = message.mentions.users.first();
            if (!user) return message.reply('Please mention a user to unmute.');
            const settings = config[message.guild.id];
            if (!settings || !settings.muteRole) return message.reply('Mute role not set.');
            const muteRole = message.guild.roles.cache.get(settings.muteRole);
            if (!muteRole) return message.reply('Mute role not found.');
            const member = message.guild.members.cache.get(user.id);
            member.roles.remove(muteRole).then(() => {
                message.reply(`${user.tag} has been unmuted.`);
                logAction('Unmute', user, message.author, 'Unmuted', message.guild);
            }).catch(err => {
                message.reply('I was unable to unmute the member. Check my permissions.');
                console.error(err);
            });
        } else if (command === 'warn') {
            if (!message.member.hasPermission('MANAGE_MESSAGES')) return message.reply('You need Manage Messages permission.');
            const user = message.mentions.users.first();
            if (!user) return message.reply('Please mention a user to warn.');
            const reason = args.slice(1).join(' ') || 'No reason provided';
            user.send(`You have been warned in ${message.guild.name} for: ${reason}`).catch(err => {
                message.reply('I couldn’t DM the user.');
            });
            message.reply(`${user.tag} has been warned.`);
            logAction('Warn', user, message.author, reason, message.guild);
        }

        // Setup Commands
        else if (command === 'setwelcome') {
            if (!message.member.hasPermission('ADMINISTRATOR')) return message.reply('You need Administrator permission.');
            const channel = message.mentions.channels.first();
            if (!channel) return message.reply('Please mention a channel.');
            config[message.guild.id] = config[message.guild.id] || {};
            config[message.guild.id].welcomeChannel = channel.id;
            fs.writeFileSync('config.json', JSON.stringify(config, null, 2));
            message.reply(`Welcome channel set to ${channel}`);
        } else if (command === 'setlog') {
            if (!message.member.hasPermission('ADMINISTRATOR')) return message.reply('You need Administrator permission.');
            const channel = message.mentions.channels.first();
            if (!channel) return message.reply('Please mention a channel.');
            config[message.guild.id] = config[message.guild.id] || {};
            config[message.guild.id].logChannel = channel.id;
            fs.writeFileSync('config.json', JSON.stringify(config, null, 2));
            message.reply(`Log channel set to ${channel}`);
        } else if (command === 'setmute') {
            if (!message.member.hasPermission('ADMINISTRATOR')) return message.reply('You need Administrator permission.');
            const role = message.mentions.roles.first();
            if (!role) return message.reply('Please mention a role.');
            config[message.guild.id] = config[message.guild.id] || {};
            config[message.guild.id].muteRole = role.id;
            fs.writeFileSync('config.json', JSON.stringify(config, null, 2));
            message.reply(`Mute role set to ${role}`);
        } else if (command === 'setverify') {
            if (!message.member.hasPermission('ADMINISTRATOR')) return message.reply('You need Administrator permission.');
            const channel = message.mentions.channels.first();
            const unverifiedRole = message.mentions.roles.first();
            const memberRole = message.mentions.roles.array()[1];
            if (!channel || !unverifiedRole || !memberRole) return message.reply('Please mention a channel, unverified role, and member role.');
            channel.send('React to this message with ✅ to verify.').then(sentMessage => {
                sentMessage.react('✅');
                config[message.guild.id] = config[message.guild.id] || {};
                config[message.guild.id].verification = {
                    channel: channel.id,
                    message: sentMessage.id,
                    unverifiedRole: unverifiedRole.id,
                    memberRole: memberRole.id
                };
                fs.writeFileSync('config.json', JSON.stringify(config, null, 2));
                message.reply('Verification set up successfully.');
            }).catch(err => {
                message.reply('Failed to set up verification. Check my permissions.');
                console.error(err);
            });
        }

        // Help Command
        else if (command === 'help') {
            const embed = new Discord.MessageEmbed()
                .setColor('#0099ff')
                .setTitle('Bot Commands')
                .setDescription('Here’s what I can do:')
                .addFields(
                    { name: '!kick @user [reason]', value: 'Kick a user from the server', inline: false },
                    { name: '!ban @user [reason]', value: 'Ban a user from the server', inline: false },
                    { name: '!mute @user', value: 'Mute a user', inline: false },
                    { name: '!unmute @user', value: 'Unmute a user', inline: false },
                    { name: '!warn @user [reason]', value: 'Warn a user', inline: false },
                    { name: '!setwelcome #channel', value: 'Set the welcome channel', inline: false },
                    { name: '!setlog #channel', value: 'Set the log channel', inline: false },
                    { name: '!setmute @role', value: 'Set the mute role', inline: false },
                    { name: '!setverify #channel @unverifiedRole @memberRole', value: 'Set up verification', inline: false }
                )
                .setTimestamp();
            message.channel.send({ embeds: [embed] });
        }

        // Unknown Command
        else {
            message.reply('Unknown command. Use !help to see available commands.');
        }
    }
});

// Welcome New Members
client.on('guildMemberAdd', member => {
    const settings = config[member.guild.id];
    if (settings && settings.welcomeChannel) {
        const channel = member.guild.channels.cache.get(settings.welcomeChannel);
        if (channel) {
            const embed = new Discord.MessageEmbed()
                .setColor('#00ff00')
                .setTitle('Welcome!')
                .setDescription(`Welcome to the server, ${member}!`)
                .setTimestamp();
            channel.send({ embeds: [embed] });
        }
    }
    if (settings && settings.verification) {
        member.roles.add(settings.verification.unverifiedRole).catch(err => console.error('Failed to add unverified role:', err));
        const verificationChannel = member.guild.channels.cache.get(settings.verification.channel);
        if (verificationChannel) {
            verificationChannel.send(`Welcome ${member}, please react to the verification message with ✅ to gain access.`);
        }
    }
});

// Handle Verification Reactions
client.on('messageReactionAdd', (reaction, user) => {
    if (user.bot) return;
    const guild = reaction.message.guild;
    if (!guild) return;
    const settings = config[guild.id];
    if (!settings || !settings.verification) return;
    if (reaction.message.id === settings.verification.message && reaction.emoji.name === '✅') {
        const member = guild.members.cache.get(user.id);
        if (member) {
            member.roles.remove(settings.verification.unverifiedRole).catch(err => console.error('Failed to remove unverified role:', err));
            member.roles.add(settings.verification.memberRole).catch(err => console.error('Failed to add member role:', err));
        }
    }
});

// Log Moderation Actions with Embeds
function logAction(action, user, moderator, reason, guild) {
    const settings = config[guild.id];
    if (settings && settings.logChannel) {
        const logChannel = guild.channels.cache.get(settings.logChannel);
        if (logChannel) {
            const embed = new Discord.MessageEmbed()
                .setColor('#ff0000')
                .setTitle(`${action} Log`)
                .addFields(
                    { name: 'User', value: user.tag, inline: true },
                    { name: 'Moderator', value: moderator.tag, inline: true },
                    { name: 'Reason', value: reason, inline: false }
                )
                .setTimestamp();
            logChannel.send({ embeds: [embed] });
        }
    }
}

// Login to Discord
client.login('YOUR_BOT_TOKEN');
