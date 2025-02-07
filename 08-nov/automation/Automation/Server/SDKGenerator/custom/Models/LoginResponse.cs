// Code generated by Microsoft (R) AutoRest Code Generator (autorest: 3.0.6262, generator: {generator})
// Changes may cause incorrect behavior and will be lost if the code is regenerated.

namespace Commvault.API.Models
{
    using static Commvault.API.Runtime.Extensions;

    /// <summary>LoginResponse</summary>
    public partial class LoginResponse :
        Commvault.API.Models.ILoginResponse,
        Commvault.API.Models.ILoginResponseInternal
    {

        /// <summary>Backing field for <see cref="AliasName" /> property.</summary>
        private string _aliasName;

        [Commvault.API.Origin(Commvault.API.PropertyOrigin.Owned)]
        public string AliasName { get => this._aliasName; set => this._aliasName = value; }

        /// <summary>Backing field for <see cref="Capability" /> property.</summary>
        private float _capability;

        [Commvault.API.Origin(Commvault.API.PropertyOrigin.Owned)]
        public float Capability { get => this._capability; set => this._capability = value; }

        /// <summary>Backing field for <see cref="Ccn" /> property.</summary>
        private float _ccn;

        [Commvault.API.Origin(Commvault.API.PropertyOrigin.Owned)]
        public float Ccn { get => this._ccn; set => this._ccn = value; }

        /// <summary>Backing field for <see cref="ErrList" /> property.</summary>
        private string[] _errList;

        [Commvault.API.Origin(Commvault.API.PropertyOrigin.Owned)]
        public string[] ErrList { get => this._errList; set => this._errList = value; }

        /// <summary>Backing field for <see cref="ForcePasswordChange" /> property.</summary>
        private bool _forcePasswordChange;

        [Commvault.API.Origin(Commvault.API.PropertyOrigin.Owned)]
        public bool ForcePasswordChange { get => this._forcePasswordChange; set => this._forcePasswordChange = value; }

        /// <summary>Backing field for <see cref="IsAccountLocked" /> property.</summary>
        private bool _isAccountLocked;

        [Commvault.API.Origin(Commvault.API.PropertyOrigin.Owned)]
        public bool IsAccountLocked { get => this._isAccountLocked; set => this._isAccountLocked = value; }

        /// <summary>Backing field for <see cref="LoginAttempts" /> property.</summary>
        private float _loginAttempts;

        [Commvault.API.Origin(Commvault.API.PropertyOrigin.Owned)]
        public float LoginAttempts { get => this._loginAttempts; set => this._loginAttempts = value; }

        /// <summary>Backing field for <see cref="ProviderType" /> property.</summary>
        private float _providerType;

        [Commvault.API.Origin(Commvault.API.PropertyOrigin.Owned)]
        public float ProviderType { get => this._providerType; set => this._providerType = value; }

        /// <summary>Backing field for <see cref="RemainingLockTime" /> property.</summary>
        private float _remainingLockTime;

        [Commvault.API.Origin(Commvault.API.PropertyOrigin.Owned)]
        public float RemainingLockTime { get => this._remainingLockTime; set => this._remainingLockTime = value; }

        /// <summary>Backing field for <see cref="SmtpAddress" /> property.</summary>
        private string _smtpAddress;

        [Commvault.API.Origin(Commvault.API.PropertyOrigin.Owned)]
        public string SmtpAddress { get => this._smtpAddress; set => this._smtpAddress = value; }

        /// <summary>Backing field for <see cref="Token" /> property.</summary>
        private string _token;

        [Commvault.API.Origin(Commvault.API.PropertyOrigin.Owned)]
        public string Token { get => this._token; set => this._token = value; }

        /// <summary>Backing field for <see cref="UserGuid" /> property.</summary>
        private string _userGuid;

        [Commvault.API.Origin(Commvault.API.PropertyOrigin.Owned)]
        public string UserGuid { get => this._userGuid; set => this._userGuid = value; }

        /// <summary>Backing field for <see cref="UserName" /> property.</summary>
        private string _userName;

        [Commvault.API.Origin(Commvault.API.PropertyOrigin.Owned)]
        public string UserName { get => this._userName; set => this._userName = value; }

        /// <summary>Creates an new <see cref="LoginResponse" /> instance.</summary>
        public LoginResponse()
        {

        }
    }
    /// LoginResponse
    public partial interface ILoginResponse :
        Commvault.API.Runtime.IJsonSerializable
    {
        [Commvault.API.Runtime.Info(
        Required = true,
        ReadOnly = false,
        Description = @"",
        SerializedName = @"aliasName",
        PossibleTypes = new [] { typeof(string) })]
        string AliasName { get; set; }

        [Commvault.API.Runtime.Info(
        Required = true,
        ReadOnly = false,
        Description = @"",
        SerializedName = @"capability",
        PossibleTypes = new [] { typeof(float) })]
        float Capability { get; set; }

        [Commvault.API.Runtime.Info(
        Required = true,
        ReadOnly = false,
        Description = @"",
        SerializedName = @"ccn",
        PossibleTypes = new [] { typeof(float) })]
        float Ccn { get; set; }

        [Commvault.API.Runtime.Info(
        Required = true,
        ReadOnly = false,
        Description = @"",
        SerializedName = @"errList",
        PossibleTypes = new [] { typeof(string) })]
        string[] ErrList { get; set; }

        [Commvault.API.Runtime.Info(
        Required = true,
        ReadOnly = false,
        Description = @"",
        SerializedName = @"forcePasswordChange",
        PossibleTypes = new [] { typeof(bool) })]
        bool ForcePasswordChange { get; set; }

        [Commvault.API.Runtime.Info(
        Required = true,
        ReadOnly = false,
        Description = @"",
        SerializedName = @"isAccountLocked",
        PossibleTypes = new [] { typeof(bool) })]
        bool IsAccountLocked { get; set; }

        [Commvault.API.Runtime.Info(
        Required = true,
        ReadOnly = false,
        Description = @"",
        SerializedName = @"loginAttempts",
        PossibleTypes = new [] { typeof(float) })]
        float LoginAttempts { get; set; }

        [Commvault.API.Runtime.Info(
        Required = true,
        ReadOnly = false,
        Description = @"",
        SerializedName = @"providerType",
        PossibleTypes = new [] { typeof(float) })]
        float ProviderType { get; set; }

        [Commvault.API.Runtime.Info(
        Required = true,
        ReadOnly = false,
        Description = @"",
        SerializedName = @"remainingLockTime",
        PossibleTypes = new [] { typeof(float) })]
        float RemainingLockTime { get; set; }

        [Commvault.API.Runtime.Info(
        Required = true,
        ReadOnly = false,
        Description = @"",
        SerializedName = @"smtpAddress",
        PossibleTypes = new [] { typeof(string) })]
        string SmtpAddress { get; set; }

        [Commvault.API.Runtime.Info(
        Required = true,
        ReadOnly = false,
        Description = @"",
        SerializedName = @"token",
        PossibleTypes = new [] { typeof(string) })]
        string Token { get; set; }

        [Commvault.API.Runtime.Info(
        Required = true,
        ReadOnly = false,
        Description = @"",
        SerializedName = @"userGUID",
        PossibleTypes = new [] { typeof(string) })]
        string UserGuid { get; set; }

        [Commvault.API.Runtime.Info(
        Required = true,
        ReadOnly = false,
        Description = @"",
        SerializedName = @"userName",
        PossibleTypes = new [] { typeof(string) })]
        string UserName { get; set; }

    }
    /// LoginResponse
    internal partial interface ILoginResponseInternal

    {
        string AliasName { get; set; }

        float Capability { get; set; }

        float Ccn { get; set; }

        string[] ErrList { get; set; }

        bool ForcePasswordChange { get; set; }

        bool IsAccountLocked { get; set; }

        float LoginAttempts { get; set; }

        float ProviderType { get; set; }

        float RemainingLockTime { get; set; }

        string SmtpAddress { get; set; }

        string Token { get; set; }

        string UserGuid { get; set; }

        string UserName { get; set; }

    }
}